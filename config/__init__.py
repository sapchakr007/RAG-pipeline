"""
Config package initialization
"""
from .settings import *

__all__ = [
    'GEMINI_API_KEY',
    'GEMINI_MODEL',
    'EMBEDDING_DIMENSION',
    'PROJECT_ROOT',
    'DATA_DIR',
    'PDF_DIR',
    'VECTOR_STORE_DIR',
    'CHUNK_SIZE',
    'CHUNK_OVERLAP',
    'MIN_CHUNK_SIZE',
    'VECTOR_DB_NAME',
    'VECTOR_DB_TYPE',
    'SIMILARITY_THRESHOLD',
    'TOP_K_RESULTS',
    'LOG_LEVEL'
]
