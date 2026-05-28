"""
Quick Start Guide for RAG Pipeline
Follow these steps to get started quickly
"""

# QUICK START STEPS
# ================

# 1. INSTALL DEPENDENCIES
# Run this command in your terminal from the RAG-pipeline directory:
# 
#    pip install -r requirements.txt
#
# This will install:
# - PyPDF2: For PDF text extraction
# - google-generativeai: For Gemini API integration
# - chromadb: For vector database storage
# - And other required packages

# 2. PREPARE YOUR PDFS
# Place your PDF files in: data/pdfs/
# You can copy PDFs here like:
# 
#    cp /path/to/your/document.pdf data/pdfs/
#
# The pipeline will process all PDFs in this directory

# 3. API KEY
# Your Gemini API key is already configured:
#
#    AIzaSyC2OUGzujkOhkBMZmbXfMjNGw3SGx2fVpM
#
# This is set in config/settings.py

# 4. RUN THE PIPELINE
# Option A - Run basic pipeline:
#
#    python main.py
#
# Option B - Run with examples:
#
#    python example_usage.py
#
# Option C - Use in your own script:
#
#    from src.rag_pipeline import RAGPipeline
#    from config.settings import *
#
#    pipeline = RAGPipeline(config)
#    pipeline.ingest_pdf('data/pdfs/document.pdf')
#    results = pipeline.retrieve("your query")

# 5. QUERY YOUR DOCUMENTS
# After ingestion, you can query your documents:
#
#    pipeline.retrieve("What is X?", top_k=5)
#
# This returns the 5 most relevant chunks from your documents

# DIRECTORY STRUCTURE
# ===================
# 
# RAG-pipeline/
# ├── src/
# │   ├── pdf_loader.py      # Load PDFs
# │   ├── chunker.py         # Split into chunks
# │   ├── embedder.py        # Create embeddings
# │   ├── vector_db.py       # Store embeddings
# │   └── rag_pipeline.py    # Main orchestration
# │
# ├── config/
# │   └── settings.py        # Configuration
# │
# ├── data/
# │   ├── pdfs/              # Place PDFs here
# │   └── vector_store/      # Embeddings stored here
# │
# ├── main.py                # Run the pipeline
# ├── example_usage.py       # See examples
# └── requirements.txt       # Dependencies

# BASIC USAGE EXAMPLE
# ===================

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    GEMINI_API_KEY, GEMINI_MODEL, PDF_DIR, 
    VECTOR_STORE_DIR, CHUNK_SIZE, CHUNK_OVERLAP
)
from src.rag_pipeline import RAGPipeline

def quick_start_example():
    """Quick start example"""
    
    # 1. Initialize pipeline
    config = {
        'gemini_api_key': GEMINI_API_KEY,
        'embedding_model': GEMINI_MODEL,
        'vector_db_path': str(VECTOR_STORE_DIR),
        'chunk_size': CHUNK_SIZE,
        'chunk_overlap': CHUNK_OVERLAP
    }
    pipeline = RAGPipeline(config)
    
    # 2. Ingest PDFs from data/pdfs/
    print("Ingesting PDFs...")
    results = pipeline.ingest_multiple_pdfs(str(PDF_DIR))
    print(f"Ingested {results.get('successful')} PDFs")
    
    # 3. Search for relevant documents
    query = "What is the main topic?"
    print(f"\nSearching for: '{query}'")
    results = pipeline.retrieve(query, top_k=3)
    
    # 4. Display results
    for i, result in enumerate(results, 1):
        print(f"\n[Result {i}]")
        print(f"Content: {result['content'][:200]}...")
        print(f"Source: {result['metadata']['source']}")

# TROUBLESHOOTING
# ===============
#
# Issue: "No module named 'PyPDF2'"
# Solution: Run `pip install -r requirements.txt`
#
# Issue: "API key is invalid"
# Solution: Check the API key in config/settings.py
#
# Issue: "No PDFs found"
# Solution: Place PDFs in data/pdfs/ directory
#
# Issue: "Permission denied on vector_store"
# Solution: Check file permissions or delete vector_store/ and rerun

# NEXT STEPS
# ==========
# 1. Place your PDF files in data/pdfs/
# 2. Run: python main.py
# 3. Or try examples: python example_usage.py
# 4. Customize config/settings.py for your needs
# 5. Check README.md for detailed documentation

print(__doc__)
print("\nTo get started:")
print("1. Place PDFs in data/pdfs/")
print("2. Run: python main.py")
print("3. Or try: python example_usage.py")
