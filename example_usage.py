"""
Example usage of the RAG Pipeline
Demonstrates how to use the pipeline for ingestion and retrieval
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    PDF_DIR,
    VECTOR_STORE_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_RESULTS
)
from src.rag_pipeline import RAGPipeline


def example_basic_usage():
    """Basic usage example"""
    print("=" * 60)
    print("RAG PIPELINE - BASIC USAGE EXAMPLE")
    print("=" * 60)
    
    # Step 1: Initialize pipeline
    print("\n[Step 1] Initializing RAG Pipeline...")
    config = {
        'gemini_api_key': GEMINI_API_KEY,
        'embedding_model': GEMINI_MODEL,
        'vector_db_path': str(VECTOR_STORE_DIR),
        'vector_db_name': 'rag_documents',
        'chunk_size': CHUNK_SIZE,
        'chunk_overlap': CHUNK_OVERLAP
    }
    
    pipeline = RAGPipeline(config)
    print("✓ Pipeline initialized successfully")
    
    # Step 2: Get initial stats
    print("\n[Step 2] Checking initial pipeline statistics...")
    stats = pipeline.get_stats()
    print(f"  Documents in vector database: {stats.get('total_documents', 0)}")
    print(f"  Vector DB path: {stats.get('vector_db_path')}")
    
    return pipeline


def example_ingest_pdf(pipeline, pdf_path: str):
    """Example: Ingest a single PDF"""
    print(f"\n[Step 3] Ingesting PDF: {pdf_path}")
    
    if not Path(pdf_path).exists():
        print(f"  ⚠ PDF file not found: {pdf_path}")
        print(f"  → Place your PDF in: {PDF_DIR}")
        return None
    
    result = pipeline.ingest_pdf(pdf_path)
    
    if result.get('status') == 'success':
        print(f"✓ PDF ingested successfully")
        print(f"  - File: {result.get('pdf_file')}")
        print(f"  - Total chunks created: {result.get('total_chunks')}")
        print(f"  - Documents stored: {result.get('documents_stored')}")
        print(f"  - Text length: {result.get('text_length')} characters")
    else:
        print(f"✗ Error ingesting PDF: {result.get('error')}")
    
    return result


def example_ingest_batch(pipeline):
    """Example: Ingest multiple PDFs from directory"""
    print(f"\n[Step 4] Batch ingesting PDFs from: {PDF_DIR}")
    
    if not Path(PDF_DIR).exists():
        print(f"  ⚠ PDF directory not found")
        return None
    
    pdf_files = list(Path(PDF_DIR).glob("*.pdf"))
    if not pdf_files:
        print(f"  ⚠ No PDF files found in {PDF_DIR}")
        return None
    
    results = pipeline.ingest_multiple_pdfs(str(PDF_DIR))
    
    print(f"✓ Batch ingestion completed")
    print(f"  - Total files processed: {results.get('total_files')}")
    print(f"  - Successful: {results.get('successful')}")
    print(f"  - Failed: {results.get('failed')}")
    print(f"  - Total chunks created: {results.get('total_chunks')}")
    print(f"  - Total documents stored: {results.get('total_stored')}")
    
    return results


def example_retrieve(pipeline, query: str):
    """Example: Retrieve relevant documents"""
    print(f"\n[Step 5] Retrieving documents for query: '{query}'")
    
    stats = pipeline.get_stats()
    if stats.get('total_documents', 0) == 0:
        print("  ⚠ No documents in vector database. Please ingest PDFs first.")
        return []
    
    results = pipeline.retrieve(query, top_k=TOP_K_RESULTS)
    
    if results:
        print(f"✓ Retrieved {len(results)} relevant documents:\n")
        for i, result in enumerate(results, 1):
            print(f"  [{i}] Document ID: {result['id']}")
            print(f"      Source: {result['metadata'].get('source', 'unknown')}")
            print(f"      Content preview: {result['content'][:150]}...")
            if result.get('distance'):
                print(f"      Relevance score: {result['distance']:.4f}")
            print()
    else:
        print("  No relevant documents found.")
    
    return results


def example_statistics(pipeline):
    """Example: Get pipeline statistics"""
    print("\n[Step 6] Pipeline Statistics")
    stats = pipeline.get_stats()
    
    print("=" * 60)
    print(f"  Total documents: {stats.get('total_documents', 0)}")
    print(f"  Collection name: {stats.get('collection_name')}")
    print(f"  Embedding model: {stats.get('embedding_model')}")
    print(f"  Vector DB path: {stats.get('vector_db_path')}")
    print("=" * 60)


def example_interactive_queries(pipeline):
    """Example: Interactive query mode"""
    print("\n" + "=" * 60)
    print("INTERACTIVE QUERY MODE")
    print("=" * 60)
    print("Enter queries to search the vector database (type 'exit' to quit)")
    
    stats = pipeline.get_stats()
    if stats.get('total_documents', 0) == 0:
        print("⚠ No documents in vector database. Please ingest PDFs first.")
        return
    
    while True:
        try:
            query = input("\nEnter your query: ").strip()
            if query.lower() == 'exit':
                print("Exiting interactive mode...")
                break
            
            if not query:
                print("Please enter a valid query.")
                continue
            
            results = pipeline.retrieve(query, top_k=3)
            
            if results:
                print(f"\nTop {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"\n  [{i}] {result['content'][:200]}...")
            else:
                print("No relevant documents found for your query.")
                
        except KeyboardInterrupt:
            print("\n\nExiting interactive mode...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")


def main():
    """Main execution"""
    try:
        # Example 1: Initialize pipeline
        pipeline = example_basic_usage()
        
        # Example 2: Ingest batch of PDFs
        example_ingest_batch(pipeline)
        
        # Example 3: Retrieve documents
        example_retrieve(
            pipeline,
            "What is the main topic of this document?"
        )
        
        # Example 4: Another retrieval example
        example_retrieve(
            pipeline,
            "Tell me about the important concepts"
        )
        
        # Example 5: Show statistics
        example_statistics(pipeline)
        
        # Example 6: Interactive mode
        try:
            example_interactive_queries(pipeline)
        except EOFError:
            print("Interactive mode ended.")
        
        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
