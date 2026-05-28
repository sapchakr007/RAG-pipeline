"""
Complete RAG Pipeline Demo - End-to-end working script
PDF Ingestion → Chunking → Embedding → Storage → Retrieval → Answer Generation
"""
import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,  # Changed log level to DEBUG for detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from config.settings import CONFIG
from src.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser(description="Run the complete RAG pipeline demo.")
    parser.add_argument(
        "-q",
        "--question",
        help="Ask one question and exit instead of entering the interactive prompt."
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip PDF ingestion and query the existing Pinecone index."
    )
    parser.add_argument(
        "--pdf-dir",
        default=CONFIG.get("pdf_dir", str(PROJECT_ROOT / "data" / "pdfs")),
        help="Directory containing PDFs to ingest."
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of retrieved chunks to use for each answer."
    )
    return parser.parse_args()


def resolve_path(path: str) -> Path:
    resolved = Path(path).expanduser()
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved


def print_answer(result):
    print("="*70)
    print(f"❓ Question: {result['question']}")
    print("="*70)
    print(f"\n💡 Answer:\n{result['answer']}\n")

    if result['source_chunks']:
        print("📚 Source Information:")
        for i, chunk in enumerate(result['source_chunks'], 1):
            source = chunk.get('metadata', {}).get('source', 'unknown')
            score = chunk.get('score', 0)
            text_preview = chunk.get('text', chunk.get('content', ''))[:100]
            print(f"  [{i}] Source: {source} | Score: {score:.4f}")
            print(f"      Preview: {text_preview}...\n")

    print("-"*70 + "\n")


def answer_question(pipeline, question: str, top_k: int):
    print("\n⏳ Processing your query...\n")
    result = pipeline.query_and_answer(question, top_k=top_k)
    print_answer(result)

def main():
    """Main execution function"""
    args = parse_args()
    
    print("\n" + "="*70)
    print("RAG PIPELINE - COMPLETE DEMO")
    print("="*70)
    
    # ===== STEP 1: Initialize Pipeline =====
    print("\n[STEP 1] Initializing RAG Pipeline...")
    try:
        pipeline = RAGPipeline(config=CONFIG)
        print("✓ Pipeline initialized successfully")
        
        # Display AI model information
        model_info = pipeline.get_model_info()
        print(f"\n  📊 AI Models Being Used:")
        print(f"     • LLM Provider:     {model_info['provider']}")
        print(f"     • Embedding Model:  {model_info['embedding_model']}")
        print(f"     • Generation Model: {model_info['generation_model']}\n")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        sys.exit(1)
    
    total_chunks = 0
    total_stored = 0

    if args.skip_ingest:
        print("[STEP 2] Skipping PDF ingestion; using existing Pinecone index...")
        stats = pipeline.get_stats()
        total_stored = stats.get("total_documents", 0)
        print(f"  Existing vectors in Pinecone: {total_stored}\n")
    else:
        # ===== STEP 2: Ingest PDFs from data/pdfs/ folder =====
        pdf_dir = resolve_path(args.pdf_dir)
        print(f"[STEP 2] Ingesting PDFs from {pdf_dir}...")
        
        if not pdf_dir.exists():
            print(f"✗ PDF directory not found: {pdf_dir}")
            sys.exit(1)
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"✗ No PDF files found in {pdf_dir}")
            sys.exit(1)
        
        print(f"Found {len(pdf_files)} PDF file(s):\n")
        
        for pdf_file in pdf_files:
            pdf_path = str(pdf_file)
            print(f"  → Processing: {pdf_file.name}")
            
            try:
                result = pipeline.ingest_pdf(pdf_path)
                
                if result.get("status") == "success":
                    chunks = result.get("total_chunks", 0)
                    stored = result.get("stored_chunks", 0)
                    total_chunks += chunks
                    total_stored += stored
                    print(f"    ✓ Chunks created: {chunks}, Stored: {stored}")
                else:
                    print(f"    ✗ Ingestion failed")
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
                print(f"    ✗ Error: {str(e)[:100]}")
        
        print(f"\n✓ Ingestion complete!")
        print(f"  Total chunks: {total_chunks}")
        print(f"  Total stored in Pinecone: {total_stored}\n")
    
    if total_stored == 0:
        print("⚠ No documents stored. Cannot proceed with queries.")
        sys.exit(1)

    if args.question:
        answer_question(pipeline, args.question, args.top_k)
        return

    if not sys.stdin.isatty():
        print("No --question provided and stdin is not interactive, so the demo is exiting.")
        print("Run with --question \"your question\" or from a terminal for interactive mode.")
        return
    
    # ===== STEP 3: Interactive Query Loop =====
    print("="*70)
    print("[STEP 3] INTERACTIVE QUERY MODE")
    print("="*70)
    print("Ask questions about your documents. Type 'exit' to quit.\n")
    
    while True:
        try:
            question = input("📝 Your question: ").strip()
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break
            
            if not question:
                continue
            
            answer_question(pipeline, question, args.top_k)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            print(f"\n✗ Error: {str(e)[:200]}\n")

if __name__ == "__main__":
    main()
