# models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import config

Base = declarative_base()

class Document(Base):
    """Document model for storing uploaded files and their content"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(50))
    content = Column(Text)
    document_metadata = Column(JSON, default={})  # Changed from 'metadata' to avoid SQLAlchemy reserved word
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}')>"

class DocumentChunk(Base):
    """Document chunks for better search and retrieval"""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON string of embedding vector
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Indexes
    __table_args__ = (
        Index('idx_document_chunks_document_id', 'document_id'),
    )

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"

class Conversation(Base):
    """Store chat conversations (optional, for persistence)"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    messages = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Conversation(id={self.id}, session_id='{self.session_id}')>"

# Database setup
engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if 'sqlite' in config.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
