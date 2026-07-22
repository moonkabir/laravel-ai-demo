# rag_engine.py - Qdrant Vector Database Version
import os
import json
import numpy as np
from typing import List, Dict, Optional
from groq import Groq
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import logging
from config import config
from retrieval_utils import expand_query_terms, score_chunk_relevance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    """RAG Engine with Qdrant Vector Database"""

    def __init__(self):
        # Initialize Groq client
        self.groq_client = Groq(api_key=config.GROQ_API_KEY)
        logger.info("Groq client initialized")

        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.vector_size = 384  # all-MiniLM-L6-v2 output size
            logger.info("✅ Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None
            self.vector_size = 384

        # Initialize Qdrant client
        self.qdrant_client = None
        try:
            self.qdrant_client = QdrantClient(
                url=config.QDRANT_URL,
                api_key=config.QDRANT_API_KEY or None,
                prefer_grpc=False
            )
            logger.info(f"✅ Qdrant client connected to {config.QDRANT_URL}")

            # Create collection if it doesn't exist
            self._ensure_collection()

        except Exception as e:
            logger.error(f"Qdrant initialization failed: {e}")
            self.qdrant_client = None

        # Fallback in-memory cache
        self.chunk_cache = {}

    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        if not self.qdrant_client:
            return

        collection_name = config.QDRANT_COLLECTION_NAME

        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if collection_name not in collection_names:
                # Create collection
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    ),
                    optimizers_config=models.OptimizersConfigDiff(
                        default_segment_number=2
                    ),
                    replication_factor=1,
                    write_consistency_factor=1
                )
                logger.info(f"✅ Collection '{collection_name}' created")
            else:
                logger.info(f"✅ Collection '{collection_name}' already exists")

        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")

    def add_document(self, document_id: int, chunks: List[str]):
        """Add document chunks with embeddings to Qdrant"""
        if not chunks:
            return

        try:
            # Generate embeddings
            if self.embedding_model:
                embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
                logger.info(f"Generated {len(embeddings)} embeddings")
            else:
                # Fallback: random embeddings (not recommended)
                embeddings = np.random.rand(len(chunks), self.vector_size)
                logger.warning("Using random embeddings - semantic search disabled")

            # Prepare points for Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                points.append(
                    PointStruct(
                        id=f"{document_id}_{i}",
                        vector=embedding.tolist(),
                        payload={
                            "document_id": document_id,
                            "chunk_index": i,
                            "content": chunk
                        }
                    )
                )

            # Upsert to Qdrant
            if self.qdrant_client:
                self.qdrant_client.upsert(
                    collection_name=config.QDRANT_COLLECTION_NAME,
                    points=points
                )
                logger.info(f"✅ Added {len(points)} points to Qdrant")
            else:
                # Fallback: store in memory
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    key = f"{document_id}_{i}"
                    self.chunk_cache[key] = {
                        'document_id': document_id,
                        'chunk_index': i,
                        'content': chunk,
                        'embedding': embedding.tolist()
                    }
                logger.info(f"Added {len(chunks)} chunks to in-memory cache")

        except Exception as e:
            logger.error(f"Error adding document: {e}")
            # Fallback: store without embeddings
            for i, chunk in enumerate(chunks):
                key = f"{document_id}_{i}"
                self.chunk_cache[key] = {
                    'document_id': document_id,
                    'chunk_index': i,
                    'content': chunk,
                    'embedding': None
                }

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search using vector similarity and query-term expansion for paraphrased questions"""
        try:
            expanded_terms = expand_query_terms(query)
            logger.info(f"Expanded query terms: {sorted(expanded_terms)[:10]}")

            if self.embedding_model:
                query_embedding = self.embedding_model.encode([query], show_progress_bar=False)[0]
                logger.info(f"Query embedding generated: '{query[:50]}...'")
            else:
                logger.warning("No embedding model, using keyword search fallback")
                return self._keyword_search(query, top_k)

            if self.qdrant_client:
                search_result = self.qdrant_client.query_points(
                    collection_name=config.QDRANT_COLLECTION_NAME,
                    query=query_embedding.tolist(),
                    limit=max(top_k * 2, 10),
                    with_payload=True,
                    score_threshold=0.2
                )

                chunks = []
                for point in search_result.points:
                    chunk_content = point.payload.get('content', '')
                    semantic_score = float(point.score)
                    lexical_score = score_chunk_relevance(query, chunk_content)
                    combined_score = max(semantic_score, lexical_score)
                    if combined_score > 0.2:
                        chunks.append({
                            'document_id': int(point.payload.get('document_id', 0)),
                            'chunk_index': int(point.payload.get('chunk_index', 0)),
                            'content': chunk_content,
                            'score': combined_score,
                            'semantic_score': semantic_score,
                            'lexical_score': lexical_score,
                        })

                if chunks:
                    chunks.sort(key=lambda x: x['score'], reverse=True)
                    logger.info(f"✅ Found {len(chunks)} semantically similar chunks from Qdrant")
                    return chunks[:top_k]

                logger.info("No results from Qdrant, trying keyword fallback")

            if hasattr(self, 'chunk_cache') and self.chunk_cache:
                results = []
                for key, data in self.chunk_cache.items():
                    if data.get('embedding') is not None:
                        similarity = self._cosine_similarity(query_embedding, data['embedding'])
                        lexical_score = score_chunk_relevance(query, data['content'])
                        combined_score = max(float(similarity), lexical_score)
                        if combined_score > 0.2:
                            results.append({
                                **data,
                                'score': float(combined_score),
                                'semantic_score': float(similarity),
                                'lexical_score': lexical_score,
                            })

                results.sort(key=lambda x: x['score'], reverse=True)
                if results:
                    logger.info(f"Found {len(results[:top_k])} similar chunks from memory")
                    return results[:top_k]

            return []

        except Exception as e:
            logger.error(f"Search error: {e}")
            return self._keyword_search(query, top_k)

    def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Fallback: Keyword-based search with synonyms"""
        if not hasattr(self, 'chunk_cache') or not self.chunk_cache:
            return []

        # Synonym expansion
        synonyms = {
            'technical': ['skills', 'technologies', 'programming', 'tools', 'experience'],
            'stack': ['technologies', 'tools', 'frameworks', 'platforms'],
            'skills': ['abilities', 'expertise', 'competencies', 'proficiencies'],
            'experience': ['work', 'employment', 'career', 'background'],
            'policy': ['rules', 'guidelines', 'procedures', 'regulations'],
            'benefits': ['perks', 'compensation', 'allowances', 'rewards'],
            'leave': ['vacation', 'holiday', 'time off', 'sabbatical'],
            'salary': ['pay', 'compensation', 'wage', 'income'],
            'education': ['degree', 'qualification', 'certification', 'training'],
            'project': ['initiative', 'program', 'campaign', 'assignment'],
        }

        query_lower = query.lower()
        expanded_words = set(query_lower.split())

        for word in query_lower.split():
            for key, syns in synonyms.items():
                if word in syns or word == key:
                    expanded_words.update(syns)
                    expanded_words.add(key)

        results = []
        for key, data in self.chunk_cache.items():
            content_lower = data['content'].lower()
            matches = sum(1 for word in expanded_words if word in content_lower)
            if matches > 0:
                lexical_score = score_chunk_relevance(query, data['content'])
                results.append({
                    **data,
                    'score': max(matches / len(expanded_words), lexical_score)
                })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def get_response(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Get response from Groq API"""
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=temperature,
                max_tokens=1000,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"[AI Service Error: {str(e)}]"

    def delete_document(self, document_id: int):
        """Delete document from Qdrant"""
        try:
            if self.qdrant_client:
                # Delete all points with this document_id
                self.qdrant_client.delete(
                    collection_name=config.QDRANT_COLLECTION_NAME,
                    points_selector=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
                logger.info(f"✅ Deleted document {document_id} from Qdrant")

            # Clear from cache
            if hasattr(self, 'chunk_cache'):
                keys_to_delete = [k for k in self.chunk_cache.keys() if k.startswith(f"{document_id}_")]
                for key in keys_to_delete:
                    del self.chunk_cache[key]
                logger.info(f"Deleted {len(keys_to_delete)} chunks from cache")

        except Exception as e:
            logger.error(f"Delete error: {e}")

    def clear_all(self):
        """Clear all documents"""
        try:
            if self.qdrant_client:
                self.qdrant_client.delete_collection(
                    collection_name=config.QDRANT_COLLECTION_NAME
                )
                logger.info("Cleared all documents from Qdrant")
                self._ensure_collection()  # Recreate empty collection

            if hasattr(self, 'chunk_cache'):
                self.chunk_cache = {}
                logger.info("Cleared all documents from cache")
        except Exception as e:
            logger.error(f"Clear all error: {e}")
