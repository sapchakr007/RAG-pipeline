"""
Optimized PDF Ingestion Script with Batch Processing
Processes PDFs with memory-efficient chunking and embedding
"""
import logging
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    PDF_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    LOG_LEVEL,
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX_NAME
)
from src.pdf_loader import PDFLoader
from src.fast_chunker import FastTextChunker
from src.embedder import GeminiEmbedder
from src.vector_db import VectorDatabase

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_pdf_optimized(pdf_path: str, batch_size: int = 5):
    """
    Process a single PDF with optimized batch embedding
    
    Args:
        pdf_path: Path to PDF file
        batch_size: Number of chunks to embed at once
    """
    try:
        logger.info(f"Starting optimized ingestion: {pdf_path}")
        
        # Initialize components
        pdf_loader = PDFLoader()
        chunker = FastTextChunker(chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        embedder = GeminiEmbedder(api_key=GEMINI_API_KEY, model=GEMINI_MODEL)
        vector_db = VectorDatabase(
            api_key=PINECONE_API_KEY,
            environment=PINECONE_ENVIRONMENT,
            index_name=PINECONE_INDEX_NAME
        )
        
        # Step 1: Load PDF
        logger.info("Step 1: Loading PDF...")
        text = pdf_loader.load_pdf(pdf_path)
        logger.info(f"PDF loaded: {len(text)} characters")
        
        # Step 2: Chunk text
        logger.info("Step 2: Chunking text...")
        source_name = Path(pdf_path).stem
        chunks = chunker.chunk_text(text, source=source_name)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Step 3: Process chunks in batches
        logger.info(f"Step 3: Creating embeddings in batches of {batch_size}...")
        total_stored = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
            
            # Create embeddings for this batch
            chunks_with_embeddings = []
            for chunk in batch:
                try:
                    embedding = embedder.create_embedding(
                        chunk['content'],
                        task_type="RETRIEVAL_DOCUMENT"
                    )
                    chunk['embedding'] = embedding
                    chunks_with_embeddings.append(chunk)
                except Exception as e:
                    logger.warning(f"Failed to embed chunk {chunk['id']}: {str(e)}")
                    continue
            
            # Store this batch in vector DB
            if chunks_with_embeddings:
                num_stored = vector_db.add_documents(chunks_with_embeddings)
                total_stored += num_stored
                logger.info(f"Batch {batch_num} stored: {num_stored} vectors")
            
            # Small delay between batches
            if i + batch_size < len(chunks):
                time.sleep(1)
        
        logger.info(f"✅ Ingestion complete! Total vectors stored: {total_stored}")
        return {
            "status": "success",
            "file": Path(pdf_path).name,
            "chunks": len(chunks),
            "vectors_stored": total_stored
        }
        
    except Exception as e:
        logger.error(f"❌ Error during ingestion: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    # Find and process all PDFs
    if PDF_DIR.exists():
        pdf_files = list(PDF_DIR.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        for pdf_file in pdf_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {pdf_file.name}")
            logger.info(f"{'='*60}\n")
            
            result = process_pdf_optimized(str(pdf_file), batch_size=5)
            logger.info(f"Result: {result}\n")
    else:
        logger.error(f"PDF directory not found: {PDF_DIR}")
