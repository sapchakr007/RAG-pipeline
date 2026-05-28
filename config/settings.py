"""
Configuration settings for RAG Pipeline
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

# Create directories if they don't exist
PDF_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()  # gemini, groq, or perplexity

# Gemini API Configuration
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "AIzaSyC2OUGzujkOhkBMZmbXfMjNGw3SGx2fVpM"  # Default from user
)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-embedding-001")
GEMINI_GENERATION_MODEL = os.getenv("GEMINI_GENERATION_MODEL", "gemini-2.5-flash")

# Perplexity API Configuration
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_BASE_URL = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
PERPLEXITY_EMBEDDING_MODEL = os.getenv("PERPLEXITY_EMBEDDING_MODEL", "pplx-embed-v1-4b")
PERPLEXITY_GENERATION_MODEL = os.getenv("PERPLEXITY_GENERATION_MODEL", "sonar-reasoning-pro")

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_EMBEDDING_MODEL = os.getenv("GROQ_EMBEDDING_MODEL", "local-hash-embedding")
GROQ_GENERATION_MODEL = os.getenv("GROQ_GENERATION_MODEL", "llama-3.3-70b-versatile")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))
if LLM_PROVIDER == "perplexity":
    EMBEDDING_MODEL = PERPLEXITY_EMBEDDING_MODEL
    GENERATION_MODEL = PERPLEXITY_GENERATION_MODEL
elif LLM_PROVIDER == "groq":
    EMBEDDING_MODEL = GROQ_EMBEDDING_MODEL
    GENERATION_MODEL = GROQ_GENERATION_MODEL
else:
    EMBEDDING_MODEL = GEMINI_MODEL
    GENERATION_MODEL = GEMINI_GENERATION_MODEL

# Reduced chunk size for testing
CHUNK_SIZE = 256  # Characters per chunk
CHUNK_OVERLAP = 50  # Overlap between chunks
MIN_CHUNK_SIZE = 100  # Minimum chunk size

# Vector Database Configuration
VECTOR_DB_NAME = "rag-documents"
VECTOR_DB_TYPE = "pinecone"  # Using Pinecone as vector database

# Pinecone Configuration
PINECONE_API_KEY = os.getenv(
    "PINECONE_API_KEY",
    "pcsk_3XinPJ_CFf1xxSwUoaHmWQSNoWyZkLdoj59wEsio7E95GN5Et6rvVWogHDExQvthaNQCfX"  # Your API key
)
PINECONE_ENVIRONMENT = os.getenv(
    "PINECONE_ENVIRONMENT",
    "us-east-1"  # Default environment - update as needed
)
PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "rag-documents"  # Index name
)

# RAG Configuration
SIMILARITY_THRESHOLD = 0.6
TOP_K_RESULTS = 5  # Number of similar documents to retrieve
EMBEDDING_BATCH_SIZE = 50

# Logging
LOG_LEVEL = "INFO"

# Consolidated Configuration Dictionary
CONFIG = {
    "llm_provider": LLM_PROVIDER,
    "gemini_api_key": GEMINI_API_KEY,
    "groq_api_key": GROQ_API_KEY,
    "groq_base_url": GROQ_BASE_URL,
    "perplexity_api_key": PERPLEXITY_API_KEY,
    "perplexity_base_url": PERPLEXITY_BASE_URL,
    "embedding_model": EMBEDDING_MODEL,
    "generation_model": GENERATION_MODEL,
    "embedding_dimension": EMBEDDING_DIMENSION,
    "embedding_batch_size": EMBEDDING_BATCH_SIZE,
    "chunk_size": CHUNK_SIZE,
    "chunk_overlap": CHUNK_OVERLAP,
    "pinecone_api_key": PINECONE_API_KEY,
    "pinecone_environment": PINECONE_ENVIRONMENT,
    "vector_db_name": PINECONE_INDEX_NAME,
    "data_dir": str(DATA_DIR),
    "pdf_dir": str(PDF_DIR),
    "vector_store_dir": str(VECTOR_STORE_DIR),
}
