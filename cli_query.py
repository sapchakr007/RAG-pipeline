#!/usr/bin/env python3
"""
RAG Pipeline - CLI Query Script
Standalone script to query ingested documents
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import CONFIG
from src.rag_pipeline import RAGPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def display_answer(question, result):
    """Display query result in formatted output"""
    print("\n" + "="*70)
    print("📖 Answer")
    print("="*70)
    print(f"\n❓ Question: {question}\n")
    print(f"💬 Answer:\n{result['answer']}")
    
    if result.get('source_chunks'):
        print("\n" + "-"*70)
        print("📌 Source Chunks:")
        print("-"*70)
        
        for i, chunk in enumerate(result['source_chunks'], 1):
            source = chunk.get('source', 'Unknown')
            score = chunk.get('score', 0)
            text = chunk.get('text', '')[:150]
            
            print(f"\n{i}. {source}")
            print(f"   Similarity Score: {score:.2f}")
            print(f"   Text: {text}...")
    
    print("\n" + "="*70 + "\n")


def main():
    """Main CLI query function"""
    parser = argparse.ArgumentParser(
        description='Query RAG Pipeline with Natural Language Questions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s "What is the main topic?"         # Single query
  %(prog)s "Question?" --top-k 5             # With custom results
  %(prog)s --interactive                     # Interactive mode
  %(prog)s --verbose                         # Show detailed info
        '''
    )
    
    parser.add_argument(
        'question',
        nargs='?',
        type=str,
        help='Question to ask about documents'
    )
    
    parser.add_argument(
        '--top-k', '-k',
        type=int,
        default=3,
        help='Number of source chunks to retrieve (default: 3)'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode - ask multiple questions'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n" + "="*70)
    print("🔍 RAG Pipeline - Document Query Tool")
    print("="*70 + "\n")
    
    try:
        # Initialize pipeline
        logger.info("Initializing RAG Pipeline...")
        pipeline = RAGPipeline(config=CONFIG)
        logger.info("✅ Pipeline initialized")
        
        # Check if documents exist
        stats = pipeline.get_stats()
        
        if stats.get('total_documents', 0) == 0:
            print("❌ Error: No documents in index!")
            print("   Please ingest PDFs first using: python cli_ingest.py")
            sys.exit(1)
        
        print(f"📚 Documents in index: {stats.get('total_documents', 0)}")
        print(f"📦 Total chunks: {stats.get('total_chunks', 0)}\n")
        
        # Show model info
        model_info = pipeline.get_model_info()
        print(f"🤖 LLM Provider: {model_info['provider']}")
        print(f"📝 Embedding Model: {model_info['embedding_model']}")
        print(f"💭 Generation Model: {model_info['generation_model']}")
        print("\n" + "="*70 + "\n")
        
        # Single query mode
        if args.question:
            result = pipeline.query_and_answer(args.question, top_k=args.top_k)
            display_answer(args.question, result)
        
        # Interactive mode
        elif args.interactive:
            print("💡 Tip: Type 'exit' to quit, 'clear' to clear screen\n")
            
            query_count = 0
            while True:
                try:
                    question = input("Your question: ").strip()
                    
                    if not question:
                        continue
                    
                    if question.lower() == 'exit':
                        break
                    
                    if question.lower() == 'clear':
                        import os
                        os.system('clear' if os.name != 'nt' else 'cls')
                        continue
                    
                    query_count += 1
                    result = pipeline.query_and_answer(question, top_k=args.top_k)
                    display_answer(question, result)
                    
                except KeyboardInterrupt:
                    print("\n")
                    break
            
            print(f"\n📊 Total queries: {query_count}")
            print("👋 Goodbye!")
        
        else:
            # No question and not interactive - show help
            parser.print_help()
            print("\nℹ️  Examples:")
            print(f"  python {Path(__file__).name} \"What is the main topic?\"")
            print(f"  python {Path(__file__).name} --interactive")
            print(f"  python {Path(__file__).name} \"Question?\" --top-k 5")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Query cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during query: {str(e)}")
        logger.exception("Query error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
