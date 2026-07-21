# rag_engine.py
import os
import json
from typing import List, Dict, Optional
from groq import Groq
import logging
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    """RAG Engine with keyword search (no embeddings, works with Python 3.14)"""

    def __init__(self):
        # Initialize Groq client
        self.groq_client = Groq(api_key=config.GROQ_API_KEY)
        logger.info("Groq client initialized")

        # In-memory cache for chunks
        self.chunk_cache = {}
        logger.info("Using keyword-based search")

    def add_document(self, document_id: int, chunks: List[str]):
        """Store document chunks in memory"""
        if not chunks:
            return

        for i, chunk in enumerate(chunks):
            key = f"{document_id}_{i}"
            self.chunk_cache[key] = {
                'document_id': document_id,
                'chunk_index': i,
                'content': chunk
            }

        logger.info(f"Added {len(chunks)} chunks for document {document_id}")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Simple keyword-based search"""
        if not self.chunk_cache:
            return []

        query_words = set(query.lower().split())
        results = []

        for key, data in self.chunk_cache.items():
            content_words = set(data['content'].lower().split())
            matches = len(query_words & content_words)
            if matches > 0:
                results.append({
                    **data,
                    'score': matches / len(query_words) if query_words else 0
                })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

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
        """Delete document from cache"""
        keys_to_delete = [k for k in self.chunk_cache.keys() if k.startswith(f"{document_id}_")]
        for key in keys_to_delete:
            del self.chunk_cache[key]
        logger.info(f"Deleted {len(keys_to_delete)} chunks for document {document_id}")
