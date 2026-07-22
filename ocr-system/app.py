# app.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import tempfile
import logging
from datetime import datetime

from config import config
from models import init_db, SessionLocal, Document, DocumentChunk, Conversation
from document_processor import DocumentProcessor
from rag_engine import RAGEngine
from utils import truncate_text, format_bytes
from server_utils import get_available_port

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ INITIALIZATION ============
# Initialize database
init_db()
logger.info("Database initialized")

# Initialize components
processor = DocumentProcessor()
rag_engine = RAGEngine()
logger.info("RAG Engine initialized")

# ============ FASTAPI APP ============
app = FastAPI(
    title="OCR & RAG Document Service",
    description="Upload documents, extract text, and chat with AI using RAG",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ PYDANTIC MODELS ============
class ChatRequest(BaseModel):
    message: str
    session_id: str
    conversation_history: Optional[List[Dict]] = []

class ChatResponse(BaseModel):
    success: bool
    reply: str
    sources: Optional[List[Dict]] = []

# ============ DEPENDENCIES ============
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============ ENDPOINTS ============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OCR & RAG Document Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health - Health check",
            "/upload-document - Upload document",
            "/chat - Chat with AI",
            "/documents - List documents",
            "/document/{id} - Get document details",
            "/document/{id} - Delete document"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "python_version": "3.14",
        "groq_api": "connected" if config.GROQ_API_KEY else "not configured",
        "vector_db": "in-memory (keyword search)",
        "documents_indexed": len(rag_engine.chunk_cache),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    db: SessionLocal = Depends(get_db)
):
    """Upload and process a document"""
    try:
        # Validate file type
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
            )

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        try:
            # Write content
            content = await file.read()
            temp_file.write(content)
            temp_file.close()

            logger.info(f"Processing file: {file.filename} ({format_bytes(len(content))})")

            # Process document
            extracted_text = processor.process_document(temp_file.name)
            logger.info(f"Extracted {len(extracted_text)} characters")

            # Get page count
            pages = processor.get_page_count(temp_file.name)

            # Save to database
            document = Document(
                title=title or file.filename,
                filename=file.filename,
                file_path=temp_file.name,
                file_type=ext[1:],
                content=extracted_text,
                document_metadata={
                    "size": len(content),
                    "pages": pages,
                    "mime_type": file.content_type
                }
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            logger.info(f"Document saved with ID: {document.id}")

            # Chunk and index
            chunks = processor.chunk_text(extracted_text)
            for idx, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    content=chunk_text
                )
                db.add(chunk)
            db.commit()

            # Add to RAG engine
            rag_engine.add_document(document.id, chunks)
            logger.info(f"Indexed {len(chunks)} chunks in RAG engine")

            return {
                "success": True,
                "message": "Document processed and indexed successfully",
                "document_id": document.id,
                "chunks": len(chunks),
                "pages": pages
            }

        finally:
            # Clean up temp file
            if os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(
    request: ChatRequest,
    db: SessionLocal = Depends(get_db)
):
    """Chat with AI using document context"""
    try:
        # Search for relevant chunks
        relevant_chunks = rag_engine.search(request.message, top_k=5)
        logger.info(f"Found {len(relevant_chunks)} relevant chunks")

        # Build context and sources
        context = ""
        sources = []

        for chunk in relevant_chunks:
            doc = db.query(Document).filter(Document.id == chunk['document_id']).first()
            if doc:
                context += f"From '{doc.title}':\n{chunk['content']}\n\n"
                sources.append({
                    "document_id": doc.id,
                    "title": doc.title,
                    "filename": doc.filename,
                    "content": truncate_text(chunk['content'], 200)
                })

        # Build system prompt
        system_prompt = """You are a helpful AI assistant that answers questions based on the company's internal documents.

Instructions:
1. Answer questions using ONLY the information provided in the context below
2. If the answer cannot be found in the context, say "I don't have information about that in our documents."
3. Be concise and direct in your responses
4. Cite the document sources when possible"""

        if context:
            system_prompt += f"\n\nContext Information:\n{context}"
        else:
            system_prompt += "\n\nNo specific context available. Politely inform the user that you don't have relevant documents."

        # Prepare messages
        messages = []

        # Add system prompt
        if not request.conversation_history or request.conversation_history[0].get("role") != "system":
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages = request.conversation_history.copy()

        # Add user message
        messages.append({"role": "user", "content": request.message})

        # Get AI response
        reply = rag_engine.get_response(messages)
        logger.info(f"AI response generated ({len(reply)} chars)")

        # Optionally save conversation
        if request.session_id:
            conv = db.query(Conversation).filter(
                Conversation.session_id == request.session_id
            ).first()

            if conv:
                history = conv.messages or []
                history.append({"role": "user", "content": request.message})
                history.append({"role": "assistant", "content": reply})
                conv.messages = history
            else:
                conv = Conversation(
                    session_id=request.session_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": request.message},
                        {"role": "assistant", "content": reply}
                    ]
                )
                db.add(conv)

            db.commit()

        return {
            "success": True,
            "reply": reply,
            "sources": sources
        }

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: SessionLocal = Depends(get_db)
):
    """List all uploaded documents"""
    try:
        documents = db.query(Document).order_by(
            Document.created_at.desc()
        ).offset(skip).limit(limit).all()

        total = db.query(Document).count()

        return {
            "success": True,
            "total": total,
            "documents": [{
                "id": doc.id,
                "title": doc.title,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "content_preview": truncate_text(doc.content, 200),
                "document_metadata": doc.document_metadata,
                "created_at": doc.created_at.isoformat(),
                "chunks": len(doc.chunks)
            } for doc in documents]
        }

    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/document/{doc_id}")
async def get_document(
    doc_id: int,
    db: SessionLocal = Depends(get_db)
):
    """Get document details including all chunks"""
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "success": True,
            "document": {
                "id": document.id,
                "title": document.title,
                "filename": document.filename,
                "file_type": document.file_type,
                "content": document.content,
                "document_metadata": document.document_metadata,
                "created_at": document.created_at.isoformat(),
                "chunks": [
                    {
                        "index": chunk.chunk_index,
                        "content": chunk.content
                    }
                    for chunk in document.chunks
                ]
            }
        }

    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/document/{doc_id}")
async def delete_document(
    doc_id: int,
    db: SessionLocal = Depends(get_db)
):
    """Delete a document"""
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Remove from RAG engine
        rag_engine.delete_document(doc_id)

        # Delete from database
        db.delete(document)
        db.commit()

        return {
            "success": True,
            "message": "Document deleted successfully"
        }

    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ RUN ============
if __name__ == "__main__":
    import uvicorn
    port = config.PORT
    try:
        port = get_available_port(port)
    except OSError:
        port = 8002

    print("\n" + "="*60)
    print("🚀 OCR & RAG Service Running")
    print("="*60)
    print(f"📁 Database: {config.DATABASE_URL}")
    print(f"🔑 Groq API: {'✓ Set' if config.GROQ_API_KEY else '✗ Not Set'}")
    print(f"🌐 Server: http://{config.HOST}:{port}")
    print("="*60 + "\n")
    uvicorn.run(app, host=config.HOST, port=port)
