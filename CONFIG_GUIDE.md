"""
Configuration Guide for RAG Pipeline
Detailed explanation of all configurable settings
"""

# SETTINGS FILE LOCATION
# ======================
# config/settings.py

# API CONFIGURATION
# =================
GEMINI_API_KEY = "AIzaSyC2OUGzujkOhkBMZmbXfMjNGw3SGx2fVpM"
# Your Google Generative AI API key
# Get one from: https://makersuite.google.com/app/apikey

GEMINI_MODEL = "models/embedding-001"
# The embedding model to use from Google Generative AI
# Current options: models/embedding-001

EMBEDDING_DIMENSION = 768
# Dimension of the embedding vectors
# For models/embedding-001: 768 dimensions


# DIRECTORY PATHS
# ===============
PROJECT_ROOT = Path(__file__).parent.parent
# Root directory of the project

PDF_DIR = PROJECT_ROOT / "data/pdfs"
# Where to place input PDF files
# Create subdirectories here if needed: data/pdfs/document1/, data/pdfs/document2/

VECTOR_STORE_DIR = PROJECT_ROOT / "data/vector_store"
# Where ChromaDB stores the vector embeddings
# This directory is created automatically


# CHUNKING CONFIGURATION
# ======================
# These settings control how documents are split into chunks

CHUNK_SIZE = 1000
# Number of characters per chunk
# Smaller values (500-1000): More chunks, better for precise retrieval
# Larger values (2000-5000): Fewer chunks, more context per chunk
# Recommended: 1000-2000

CHUNK_OVERLAP = 200
# Number of overlapping characters between consecutive chunks
# Prevents cutting important concepts in the middle
# Usually 10-30% of CHUNK_SIZE
# Example: if CHUNK_SIZE=1000, CHUNK_OVERLAP=200

MIN_CHUNK_SIZE = 100
# Minimum characters for a chunk to be considered valid
# Smaller chunks are filtered out
# Prevents storing empty or trivial chunks


# VECTOR DATABASE CONFIGURATION
# ==============================
# Settings for persistent storage and retrieval

VECTOR_DB_NAME = "rag_documents"
# Name of the collection in ChromaDB
# Use different names for different document sets

VECTOR_DB_TYPE = "chromadb"
# Vector database type
# Currently supporting: chromadb
# Future: pinecone, weaviate, milvus

SIMILARITY_THRESHOLD = 0.6
# Minimum similarity score (0.0-1.0) for results
# Higher value = more strict matching
# Lower value = broader matching


# RETRIEVAL CONFIGURATION
# =======================
TOP_K_RESULTS = 5
# Default number of results to return for queries
# Can be overridden per query
# More results = broader context, slower retrieval
# Fewer results = faster retrieval, less context


# LOGGING CONFIGURATION
# =====================
LOG_LEVEL = "INFO"
# Logging verbosity
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
# DEBUG: Very detailed logging (development)
# INFO: Standard logging (recommended)
# WARNING: Only warnings and errors
# ERROR: Only errors
# CRITICAL: Only critical errors


# CUSTOMIZATION EXAMPLES
# ======================

# EXAMPLE 1: For Large Documents
# If processing large academic papers, use:
# CHUNK_SIZE = 2000           # Larger chunks for better context
# CHUNK_OVERLAP = 300         # More overlap to avoid splitting concepts
# TOP_K_RESULTS = 3           # Fewer results but more comprehensive

# EXAMPLE 2: For Q&A Use Cases
# If using for question-answering systems:
# CHUNK_SIZE = 500            # Smaller chunks for precise answers
# CHUNK_OVERLAP = 50          # Less overlap needed
# TOP_K_RESULTS = 10          # More results for better coverage
# SIMILARITY_THRESHOLD = 0.7  # Stricter matching

# EXAMPLE 3: For Mixed Documents
# If processing diverse document types:
# CHUNK_SIZE = 1000           # Balanced
# CHUNK_OVERLAP = 200         # Standard overlap
# TOP_K_RESULTS = 5           # Default results
# LOG_LEVEL = "DEBUG"         # Monitor processing

# EXAMPLE 4: Production Environment
# For production systems:
# LOG_LEVEL = "WARNING"       # Less logging overhead
# SIMILARITY_THRESHOLD = 0.65 # Balanced precision/recall
# TOP_K_RESULTS = 5           # Standard results
# Use multiple vector stores with different VECTOR_DB_NAME values


# PERFORMANCE TUNING
# ==================

# For FASTER retrieval:
# - Reduce CHUNK_SIZE (smaller vectors to compare)
# - Reduce TOP_K_RESULTS (fewer results to process)
# - Reduce CHUNK_OVERLAP (fewer total chunks)
# - Set LOG_LEVEL to WARNING (less I/O)

# For BETTER accuracy:
# - Increase CHUNK_OVERLAP (more context preservation)
# - Increase TOP_K_RESULTS (broader coverage)
# - Reduce CHUNK_SIZE (more specific chunks)
# - Lower SIMILARITY_THRESHOLD (accept more results)

# For LOWER memory usage:
# - Reduce CHUNK_SIZE
# - Reduce TOP_K_RESULTS
# - Use separate vector stores for different document sets


# ENVIRONMENT VARIABLES (from .env file)
# =======================================
# You can also set these in a .env file:
#
# GEMINI_API_KEY=your_key_here
# PDF_DIRECTORY=./data/pdfs
# CHUNK_SIZE=1000
# CHUNK_OVERLAP=200
# VECTOR_DB_PATH=./data/vector_store
# TOP_K_RESULTS=5
# SIMILARITY_THRESHOLD=0.6
# LOG_LEVEL=INFO
#
# These will override the defaults in settings.py


# HOW TO CHANGE SETTINGS
# ======================

# Method 1: Edit config/settings.py directly
# Edit the file and change the values you want
# Changes take effect when you restart the pipeline

# Method 2: Use .env file
# Create a .env file in the project root
# Settings from .env override settings.py

# Method 3: Pass config dictionary
# When initializing RAGPipeline, pass a config dict:
#
# config = {
#     'chunk_size': 1500,
#     'top_k_results': 3,
#     'gemini_api_key': 'your-key'
# }
# pipeline = RAGPipeline(config)


# TROUBLESHOOTING CONFIGURATIONS
# ===============================

# Problem: "Too few results returned"
# Solution: Increase TOP_K_RESULTS or lower SIMILARITY_THRESHOLD

# Problem: "Irrelevant results returned"
# Solution: Increase SIMILARITY_THRESHOLD or reduce CHUNK_OVERLAP

# Problem: "Memory usage too high"
# Solution: Reduce CHUNK_SIZE or use separate vector stores

# Problem: "Processing too slow"
# Solution: Reduce CHUNK_SIZE, CHUNK_OVERLAP, or TOP_K_RESULTS

# Problem: "Chunks cutting important information"
# Solution: Increase CHUNK_SIZE or CHUNK_OVERLAP

# Problem: "Too many small/empty chunks"
# Solution: Increase MIN_CHUNK_SIZE


# RECOMMENDED SETTINGS BY USE CASE
# =================================

# RESEARCH PAPERS / TECHNICAL DOCS:
# CHUNK_SIZE = 1500
# CHUNK_OVERLAP = 300
# TOP_K_RESULTS = 5
# SIMILARITY_THRESHOLD = 0.6

# NEWS ARTICLES / SHORT DOCS:
# CHUNK_SIZE = 500
# CHUNK_OVERLAP = 100
# TOP_K_RESULTS = 3
# SIMILARITY_THRESHOLD = 0.7

# CUSTOMER SUPPORT / FAQ:
# CHUNK_SIZE = 800
# CHUNK_OVERLAP = 150
# TOP_K_RESULTS = 5
# SIMILARITY_THRESHOLD = 0.65

# CODE DOCUMENTATION:
# CHUNK_SIZE = 1000
# CHUNK_OVERLAP = 200
# TOP_K_RESULTS = 5
# SIMILARITY_THRESHOLD = 0.6

# LEGAL DOCUMENTS:
# CHUNK_SIZE = 2000
# CHUNK_OVERLAP = 400
# TOP_K_RESULTS = 10
# SIMILARITY_THRESHOLD = 0.6


# SCALING CONFIGURATION
# =====================

# For single user / development:
# Current default settings are fine

# For multiple users:
# - Consider using a shared vector store
# - Use separate collections per user (VECTOR_DB_NAME)
# - Implement caching for frequent queries
# - Set LOG_LEVEL = WARNING to reduce overhead

# For very large document collections:
# - Split documents across multiple vector stores
# - Use VECTOR_DB_NAME variants: "rag_documents_part1", etc.
# - Consider batch processing with error handling
# - Monitor memory usage and adjust CHUNK_SIZE


# API RATE LIMITING
# =================
# Google Generative AI has rate limits:
# - The embedder automatically adds delays between batches
# - Default batch size: 10 requests
# - Delay between batches: 2 seconds

# To adjust rate limiting:
# Edit src/embedder.py
# Change batch_size parameter in create_embeddings_batch()
# Change time.sleep(2) delay value


print(__doc__)
