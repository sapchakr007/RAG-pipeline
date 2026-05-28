#!/usr/bin/env python3
"""
RAG Pipeline - Unified Entry Point
Central command to manage all RAG operations: ingest, query, and demo
"""
import logging
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import CONFIG, PDF_DIR
from src.rag_pipeline import RAGPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_menu():
    """Display interactive menu"""
    print("\n" + "="*70)
    print("🔍 RAG Pipeline - Main Menu")
    print("="*70)
    print("\n1. 📥 Ingest PDFs")
    print("   └─ Load PDFs from data/pdfs/ and create embeddings")
    print("\n2. 💬 Interactive Query")
    print("   └─ Ask questions about ingested documents")
    print("\n3. 🚀 Start Web UI")
    print("   └─ Launch Flask backend + React frontend")
    print("\n4. 📊 Pipeline Status")
    print("   └─ Show statistics about ingested documents")
    print("\n5. 🎓 Run Demo")
    print("   └─ See full end-to-end workflow")
    print("\n6. ❌ Exit")
    print("\n" + "="*70)


def ingest_pdfs():
    """Ingest PDFs from data/pdfs directory"""
    print("\n" + "="*70)
    print("📥 Starting PDF Ingestion...")
    print("="*70)
    
    try:
        pipeline = RAGPipeline(config=CONFIG)
        
        if not PDF_DIR.exists() or not list(PDF_DIR.glob("*.pdf")):
            print(f"\n⚠️  No PDFs found in {PDF_DIR}")
            print("   Please add PDF files to data/pdfs/")
            return
        
        result = pipeline.ingest_multiple_pdfs(str(PDF_DIR))
        
        print("\n" + "="*70)
        print("✅ Ingestion Complete!")
        print("="*70)
        print(f"Total files: {result['total_files']}")
        print(f"Successful: {result['successful']}")
        print(f"Failed: {result['failed']}")
        print(f"Total chunks stored: {result['total_chunks']}")
        
    except Exception as e:
        print(f"\n❌ Ingestion failed: {str(e)}")
        logger.exception("Ingestion error:")


def interactive_query():
    """Interactive query mode"""
    print("\n" + "="*70)
    print("💬 Interactive Query Mode")
    print("="*70)
    print("Type 'exit' to return to menu\n")
    
    try:
        pipeline = RAGPipeline(config=CONFIG)
        
        # Check if documents exist
        stats = pipeline.get_stats()
        if stats['total_documents'] == 0:
            print("⚠️  No documents in index. Please ingest PDFs first.")
            return
        
        print(f"📚 Documents in index: {stats['total_documents']}\n")
        
        while True:
            question = input("Your question: ").strip()
            
            if question.lower() == 'exit':
                break
            
            if not question:
                continue
            
            result = pipeline.query_and_answer(question, top_k=3)
            
            print("\n" + "-"*70)
            print("📖 Answer:")
            print("-"*70)
            print(result['answer'])
            
            if result['source_chunks']:
                print("\n📌 Sources:")
                for chunk in result['source_chunks']:
                    print(f"  • {chunk.get('source', 'N/A')}")
                    print(f"    Score: {chunk.get('score', 0):.2f}")
                    print(f"    Text: {chunk.get('text', '')[:100]}...")
            print("-"*70 + "\n")
            
    except Exception as e:
        print(f"\n❌ Query failed: {str(e)}")
        logger.exception("Query error:")


def start_web_ui():
    """Start Flask backend + React frontend"""
    print("\n" + "="*70)
    print("🚀 Starting Web UI...")
    print("="*70)
    print("\n🔵 Backend: http://localhost:5001")
    print("🔵 Frontend: http://localhost:3000")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        # Start Flask backend
        print("Starting Flask backend...")
        subprocess.Popen([
            sys.executable, "-m", "flask", "run", 
            "--port", "5001"
        ], cwd=str(Path(__file__).parent))
        
        # Wait a bit for Flask to start
        time.sleep(2)
        
        # Start React frontend
        print("Starting React frontend...")
        subprocess.Popen([
            "npm", "start"
        ], cwd=str(Path(__file__).parent / "frontend"),
        env={**os.environ, "BROWSER": "none"})
        
        print("\n✅ Both servers started!")
        print("Opening http://localhost:3000 in your browser...")
        webbrowser.open("http://localhost:3000")
        
        print("\nPress Ctrl+C to stop both servers")
        input()
        
    except Exception as e:
        print(f"\n❌ Failed to start UI: {str(e)}")
        logger.exception("Web UI error:")


def show_status():
    """Display pipeline status"""
    print("\n" + "="*70)
    print("📊 Pipeline Status")
    print("="*70)
    
    try:
        pipeline = RAGPipeline(config=CONFIG)
        stats = pipeline.get_stats()
        model_info = pipeline.get_model_info()
        
        print(f"\n📚 Documents: {stats['total_documents']}")
        print(f"📦 Chunks: {stats['total_chunks']}")
        
        print(f"\n🤖 LLM Provider: {model_info['provider']}")
        print(f"📝 Embedding Model: {model_info['embedding_model']}")
        print(f"💭 Generation Model: {model_info['generation_model']}")
        
        print(f"\n📁 PDF Directory: {PDF_DIR}")
        if PDF_DIR.exists():
            pdfs = list(PDF_DIR.glob("*.pdf"))
            print(f"   Files in directory: {len(pdfs)}")
            if pdfs:
                for pdf in pdfs:
                    print(f"     • {pdf.name}")
            
    except Exception as e:
        print(f"\n❌ Failed to get status: {str(e)}")
        logger.exception("Status check error:")
    
    print("\n" + "="*70)


def run_demo():
    """Run full demo"""
    print("\n" + "="*70)
    print("🎓 Running Full Demo...")
    print("="*70 + "\n")
    
    try:
        subprocess.run([sys.executable, "rag_complete_demo.py"], 
                       cwd=str(Path(__file__).parent))
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        logger.exception("Demo error:")


def main():
    """Main execution function with interactive menu"""
    print("\n" + "="*70)
    print("🚀 Welcome to RAG Pipeline")
    print("="*70)
    
    while True:
        show_menu()
        choice = input("Select an option (1-6): ").strip()
        
        if choice == "1":
            ingest_pdfs()
        elif choice == "2":
            interactive_query()
        elif choice == "3":
            start_web_ui()
        elif choice == "4":
            show_status()
        elif choice == "5":
            run_demo()
        elif choice == "6":
            print("\n👋 Thank you for using RAG Pipeline!\n")
            break
        else:
            print("\n❌ Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    import os
    main()
