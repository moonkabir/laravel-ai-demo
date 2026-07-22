# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Groq API
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./documents.db')

    # Qdrant Configuration
    QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
    QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '')
    QDRANT_COLLECTION_NAME = os.getenv('QDRANT_COLLECTION_NAME', 'documents')
    QDRANT_VECTOR_SIZE = int(os.getenv('QDRANT_VECTOR_SIZE', 384))

    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8001))

    # Tesseract (for Windows)
    TESSERACT_PATH = os.getenv('TESSERACT_PATH', '')

    # Model Settings
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 500))

    # Allowed file types
    ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.docx', '.txt']

    # CORS
    ALLOWED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ]

config = Config()
