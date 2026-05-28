#!/usr/bin/env python3
"""
RAG Pipeline - CLI Ingestion Script
Standalone script to ingest PDFs into the vector database
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import CONFIG, PDF_DIR
from src.rag_pipeline import RAGPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI ingestion function"""
    parser = argparse.ArgumentParser(
        description='Ingest PDFs into RAG Pipeline Vector Database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                      # Ingest all PDFs from data/pdfs/
  %(prog)s --file report.pdf    # Ingest a specific PDF
  %(prog)s --dir /path/to/pdfs  # Ingest from custom directory
  %(prog)s --verbose            # Show detailed logging
        '''
    )
    
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Path to a specific PDF file to ingest'
    )
    
    parser.add_argument(
        '--dir', '-d',
        type=str,
        help='Path to directory containing PDFs (default: data/pdfs/)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--skip-confirm',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n" + "="*70)
    print("📥 RAG Pipeline - PDF Ingestion Tool")
    print("="*70 + "\n")
    
    try:
        # Initialize pipeline
        logger.info("Initializing RAG Pipeline...")
        pipeline = RAGPipeline(config=CONFIG)
        logger.info("✅ Pipeline initialized")
        
        # Determine what to ingest
        if args.file:
            # Ingest single file
            pdf_path = Path(args.file)
            
            if not pdf_path.exists():
                print(f"❌ Error: File not found: {pdf_path}")
                sys.exit(1)
            
            if not pdf_path.suffix.lower() == '.pdf':
                print(f"❌ Error: File is not a PDF: {pdf_path}")
                sys.exit(1)
            
            print(f"📄 Ingesting: {pdf_path.name}")
            print(f"   Size: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")
            
            if not args.skip_confirm:
                confirm = input("\nContinue? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Cancelled.")
                    sys.exit(0)
            
            result = pipeline.ingest_pdf(str(pdf_path))
            
            print("\n" + "-"*70)
            print("✅ Ingestion Complete!")
            print("-"*70)
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Total chunks: {result.get('total_chunks', 0)}")
            print(f"Stored chunks: {result.get('stored_chunks', 0)}")
            
        else:
            # Ingest directory
            ingest_dir = Path(args.dir) if args.dir else PDF_DIR
            
            if not ingest_dir.exists():
                print(f"❌ Error: Directory not found: {ingest_dir}")
                sys.exit(1)
            
            pdf_files = list(ingest_dir.glob("*.pdf"))
            
            if not pdf_files:
                print(f"⚠️  No PDF files found in: {ingest_dir}")
                sys.exit(1)
            
            print(f"📂 Directory: {ingest_dir}")
            print(f"📊 Found {len(pdf_files)} PDF file(s):")
            
            for i, pdf in enumerate(pdf_files, 1):
                size_mb = pdf.stat().st_size / 1024 / 1024
                print(f"   {i}. {pdf.name} ({size_mb:.2f} MB)")
            
            if not args.skip_confirm:
                confirm = input(f"\nIngest all {len(pdf_files)} files? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Cancelled.")
                    sys.exit(0)
            
            result = pipeline.ingest_multiple_pdfs(str(ingest_dir))
            
            print("\n" + "-"*70)
            print("✅ Batch Ingestion Complete!")
            print("-"*70)
            print(f"Total files: {result['total_files']}")
            print(f"Successful: {result['successful']}")
            print(f"Failed: {result['failed']}")
            print(f"Total chunks: {result['total_chunks']}")
        
        # Show final statistics
        print("\n" + "-"*70)
        print("📊 Pipeline Statistics:")
        print("-"*70)
        
        stats = pipeline.get_stats()
        print(f"Total documents in index: {stats.get('total_documents', 0)}")
        print(f"Total chunks: {stats.get('total_chunks', 0)}")
        
        model_info = pipeline.get_model_info()
        print(f"\n🤖 LLM Provider: {model_info['provider']}")
        print(f"📝 Embedding Model: {model_info['embedding_model']}")
        print(f"💭 Generation Model: {model_info['generation_model']}")
        
        print("\n" + "="*70)
        print("✨ Ingestion successful! Ready for queries.")
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Ingestion cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during ingestion: {str(e)}")
        logger.exception("Ingestion error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
