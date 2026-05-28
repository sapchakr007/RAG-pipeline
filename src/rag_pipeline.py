"""
RAG Pipeline Module
Main orchestration of the retrieval-augmented generation pipeline
"""
import logging
from typing import List, Dict, Any
from pathlib import Path
import psutil  # For monitoring memory usage
import hashlib
import json
from datetime import datetime

from .pdf_loader import PDFLoader
from .chunker import TextChunker
from .transaction_extractor import TransactionExtractor
from .embedder import GeminiEmbedder, GroqEmbedder, PerplexityEmbedder
from .vector_db import VectorDatabase

logger = logging.getLogger(__name__)


class RAGPipeline:
    """End-to-end RAG Pipeline"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize RAG Pipeline
        
        Args:
            config: Configuration dictionary with settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.pdf_loader = PDFLoader()
        self.chunker = TextChunker(
            chunk_size=config.get('chunk_size', 1000),
            overlap=config.get('chunk_overlap', 200)
        )
        self.transaction_extractor = TransactionExtractor()
        provider = config.get('llm_provider', 'gemini').lower()
        if provider == 'perplexity':
            self.embedder = PerplexityEmbedder(
                api_key=config.get('perplexity_api_key'),
                model=config.get('embedding_model', 'pplx-embed-v1-4b'),
                generation_model=config.get('generation_model', 'sonar-reasoning-pro'),
                embedding_dimension=config.get('embedding_dimension', 768),
                base_url=config.get('perplexity_base_url', 'https://api.perplexity.ai')
            )
        elif provider == 'groq':
            self.embedder = GroqEmbedder(
                api_key=config.get('groq_api_key'),
                generation_model=config.get('generation_model', 'llama-3.3-70b-versatile'),
                embedding_dimension=config.get('embedding_dimension', 768),
                base_url=config.get('groq_base_url', 'https://api.groq.com/openai/v1')
            )
        else:
            self.embedder = GeminiEmbedder(
                api_key=config.get('gemini_api_key'),
                model=config.get('embedding_model', 'gemini-embedding-001'),
                generation_model=config.get('generation_model', 'gemini-2.5-flash'),
                embedding_dimension=config.get('embedding_dimension', 768)
            )
        self.vector_db = VectorDatabase(
            api_key=config.get('pinecone_api_key'),
            environment=config.get('pinecone_environment'),
            index_name=config.get('vector_db_name', 'rag-documents'),
            embedding_dimension=config.get('embedding_dimension', 768)
        )
        
        self.logger.info("RAG Pipeline initialized")
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the AI models being used
        
        Returns:
            Dictionary with provider, embedding model, and generation model
        """
        provider = self.config.get('llm_provider', 'gemini').lower()
        
        model_info = {
            'provider': provider.upper(),
            'embedding_model': self.config.get('embedding_model', 'N/A'),
            'generation_model': self.config.get('generation_model', 'N/A')
        }
        
        return model_info
    
    def log_model_info(self):
        """Log the AI models being used"""
        model_info = self.get_model_info()
        self.logger.info(f"LLM Provider: {model_info['provider']}")
        self.logger.info(f"Embedding Model: {model_info['embedding_model']}")
        self.logger.info(f"Generation Model: {model_info['generation_model']}")
    
    def log_memory_usage(self, step: str):
        """
        Log the current memory usage
        
        Args:
            step: Description of the pipeline step
        """
        process = psutil.Process()
        mem_info = process.memory_info()
        self.logger.info(f"Memory usage at {step}: {mem_info.rss / 1024 ** 2:.2f} MB")

    def calculate_md5(self, pdf_path: str) -> str:
        """Calculate the MD5 checksum of a file"""
        hasher = hashlib.md5()
        with open(pdf_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def load_processed_state(self) -> Dict[str, Any]:
        """Load state of processed files"""
        state_file = Path("data/processed_pdfs.json")
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"processed": [], "hashes": {}, "last_updated": ""}

    def save_processed_state(self, state: Dict[str, Any]):
        """Save state of processed files"""
        state_file = Path("data/processed_pdfs.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def is_pdf_processed(self, pdf_path: str) -> bool:
        """Check if a PDF has already been processed by filename or hash"""
        pdf_path = Path(pdf_path)
        state = self.load_processed_state()
        
        # Check by filename
        processed_list = state.get("processed", [])
        if pdf_path.name in processed_list:
            return True
            
        # Check by MD5 hash
        file_hash = self.calculate_md5(str(pdf_path))
        hashes = state.get("hashes", {})
        if file_hash in hashes.values():
            return True
            
        return False

    def mark_pdf_processed(self, pdf_path: str):
        """Mark a PDF as processed in the state file"""
        pdf_path = Path(pdf_path)
        state = self.load_processed_state()
        
        if "processed" not in state or not isinstance(state["processed"], list):
            state["processed"] = []
        if "hashes" not in state or not isinstance(state["hashes"], dict):
            state["hashes"] = {}
            
        if pdf_path.name not in state["processed"]:
            state["processed"].append(pdf_path.name)
            
        file_hash = self.calculate_md5(str(pdf_path))
        state["hashes"][pdf_path.name] = file_hash
        state["last_updated"] = datetime.now().isoformat()
        self.save_processed_state(state)

    def append_transactions_to_db(self, new_txns: List[Dict[str, Any]]) -> int:
        """Append extracted transactions to persistent JSON database"""
        txn_file = Path("data/transactions.json")
        txn_file.parent.mkdir(parents=True, exist_ok=True)
        
        current_txns = []
        if txn_file.exists():
            try:
                with open(txn_file, 'r') as f:
                    current_txns = json.load(f)
            except Exception:
                pass
                
        existing_ids = {t.get('id') for t in current_txns if t.get('id')}
        appended = 0
        for txn in new_txns:
            # Ensure deterministic ID based on transaction details
            if 'id' not in txn:
                raw_str = f"{txn.get('date')}_{txn.get('description')}_{txn.get('amount')}_{Path(txn.get('source')).name}"
                txn['id'] = hashlib.md5(raw_str.encode('utf-8')).hexdigest()[:12].upper()
                
            if txn['id'] not in existing_ids:
                current_txns.append(txn)
                existing_ids.add(txn['id'])
                appended += 1
                
        with open(txn_file, 'w') as f:
            json.dump(current_txns, f, indent=2)
        return appended

    def ingest_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Ingest a single PDF with idempotent tracking and automatic transaction extraction
        """
        self.logger.info(f"Ingesting PDF: {pdf_path}")
        self.log_memory_usage("start")

        # Step 0: Check if already processed (idempotency check)
        if self.is_pdf_processed(pdf_path):
            self.logger.info(f"⏭️ Skipping PDF {pdf_path} (already processed)")
            return {
                "status": "success",
                "pdf_path": pdf_path,
                "total_chunks": 0,
                "stored_chunks": 0,
                "skipped": True,
                "message": "File already processed"
            }

        try:
            # Step 1: Load PDF
            text = self.pdf_loader.load_pdf(pdf_path)
            self.logger.info(f"Loaded PDF with {len(text)} characters")
            self.log_memory_usage("after loading PDF")

            # Step 2: Try to extract structured bank transactions
            self.logger.info("Extracting transactions from PDF...")
            transactions = self.transaction_extractor.extract_transactions(text, source=pdf_path)
            
            # Detect bank name from text
            bank_name = "Unknown Bank"
            text_lower = text.lower()
            if "kotak" in text_lower:
                bank_name = "Kotak Mahindra Bank"
            elif "hdfc" in text_lower:
                bank_name = "HDFC Bank"
            elif "icici" in text_lower:
                bank_name = "ICICI Bank"
            elif "sbi" in text_lower or "state bank" in text_lower:
                bank_name = "State Bank of India"
            
            chunks = []
            if transactions:
                self.logger.info(f"Extracted {len(transactions)} structured transactions")
                
                # Enrich transactions with bank name and deterministic ID
                for txn in transactions:
                    txn['bank'] = txn.get('bank', bank_name)
                    if 'id' not in txn:
                        raw_str = f"{txn.get('date')}_{txn.get('description')}_{txn.get('amount')}_{Path(txn.get('source')).name}"
                        txn['id'] = hashlib.md5(raw_str.encode('utf-8')).hexdigest()[:12].upper()
                
                # Append to local transactions state database
                appended_count = self.append_transactions_to_db(transactions)
                self.logger.info(f"Appended {appended_count} new transactions to data/transactions.json")
                
                # Create chunks from transactions (grouped by 5)
                chunks = self.transaction_extractor.create_transaction_chunks(transactions, chunk_size=5)
                self.logger.info(f"Created {len(chunks)} transaction chunks")
            else:
                self.logger.info("No structured transactions found. Falling back to generic text chunking.")
                chunks = self.chunker.chunk_text(text, source=pdf_path)
                self.logger.info(f"Chunked text into {len(chunks)} chunks")
            
            if not chunks:
                self.logger.error("No chunks created during chunking. Aborting ingestion.")
                return {"status": "error", "message": "No chunks created"}

            # Attach metadata (bank, source, index) to the payloads
            for i, chunk in enumerate(chunks):
                if 'metadata' not in chunk:
                    chunk['metadata'] = {}
                chunk['metadata']['bank'] = bank_name
                chunk['metadata']['source'] = Path(pdf_path).name
                chunk['metadata']['chunk_index'] = i
                
                if 'text' not in chunk:
                    chunk['text'] = chunk.get('content', '')
                if 'content' not in chunk:
                    chunk['content'] = chunk.get('text', '')

            # Step 3: Generate Embeddings in Batches
            batch_size = self.config.get("embedding_batch_size", 50)
            zero_embedding = [0] * self.config.get('embedding_dimension', 768)
            self.logger.info(f"Starting embedding generation for {len(chunks)} chunks in batches of {batch_size}")
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                texts = [chunk['text'] for chunk in batch]
                self.logger.info(f"Processing batch {batch_num}/{total_batches} with {len(batch)} chunks")
                embeddings = self.embedder.create_embeddings(texts)
                
                success_count = 0
                for chunk, embedding in zip(batch, embeddings):
                    chunk['embedding'] = embedding
                    if embedding and embedding != zero_embedding:
                        success_count += 1
                
                self.logger.info(f"Completed batch {batch_num}/{total_batches}. Successful embeddings: {success_count}/{len(batch)}")
                self.log_memory_usage(f"after processing batch {batch_num}/{total_batches}")
            
            self.logger.info("Generated embeddings for all chunks in batches")

            valid_chunks = [
                chunk
                for chunk in chunks
                if chunk.get('embedding') and chunk['embedding'] != zero_embedding
            ]
            if not valid_chunks:
                self.logger.error("No valid embeddings created. Aborting vector storage.")
                return {"status": "error", "message": "No valid embeddings created"}

            # Step 4: Store in Pinecone (Upserts incrementally/non-destructively)
            self.logger.info(f"Storing {len(valid_chunks)} chunks in Pinecone")
            added_count = self.vector_db.add_documents(valid_chunks)
            self.logger.info(f"Stored {added_count} chunks in Pinecone")
            self.log_memory_usage("after storing in Pinecone")

            # Step 5: Mark PDF as processed in delta load log
            self.mark_pdf_processed(pdf_path)
            self.logger.info(f"✓ Marked {pdf_path} as processed successfully")

            return {
                "status": "success",
                "pdf_path": pdf_path,
                "total_chunks": len(chunks),
                "stored_chunks": added_count,
                "transactions_extracted": len(transactions) if transactions else 0
            }

        except Exception as e:
            self.logger.error(f"Error processing {pdf_path}: {e}")
            return {"status": "error", "error": str(e)}
    
    def ingest_multiple_pdfs(self, pdf_directory: str) -> Dict[str, Any]:
        """
        Ingest multiple PDFs from a directory
        
        Args:
            pdf_directory: Path to directory containing PDFs
            
        Returns:
            Dictionary with aggregated results
        """
        try:
            pdf_dir = Path(pdf_directory)
            pdf_files = list(pdf_dir.glob("*.pdf"))
            
            if not pdf_files:
                self.logger.warning(f"No PDF files found in {pdf_directory}")
                return {
                    "status": "warning",
                    "message": "No PDF files found"
                }
            
            results = {
                "total_files": len(pdf_files),
                "successful": 0,
                "failed": 0,
                "total_chunks": 0,
                "total_stored": 0,
                "files": []
            }
            
            for pdf_file in pdf_files:
                result = self.ingest_pdf(str(pdf_file))
                results["files"].append(result)
                
                if result["status"] == "success":
                    results["successful"] += 1
                    results["total_chunks"] += result.get("total_chunks", 0)
                    results["total_stored"] += result.get("documents_stored", 0)
                else:
                    results["failed"] += 1
            
            self.logger.info(f"Batch ingestion completed: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during batch ingestion: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def ingest_pdf_with_transactions(self, pdf_path: str, extraction_type: str = "grouped") -> Dict[str, Any]:
        """
        Ingest a PDF and extract transaction details instead of generic text chunks
        
        Args:
            pdf_path: Path to the PDF file
            extraction_type: Type of extraction - "grouped" or "summary"
                - "grouped": Groups multiple transactions together
                - "summary": Creates spending summary by category
        
        Returns:
            Metadata about the ingestion process
        """
        self.logger.info(f"Ingesting PDF with transaction extraction: {pdf_path}")
        self.log_memory_usage("start transaction extraction")
        
        try:
            # Step 1: Load PDF
            text = self.pdf_loader.load_pdf(pdf_path)
            self.logger.info(f"Loaded PDF with {len(text)} characters")
            
            # Step 2: Extract Transactions
            self.logger.info("Extracting transactions from PDF...")
            transactions = self.transaction_extractor.extract_transactions(text, source=pdf_path)
            
            if not transactions:
                self.logger.warning(f"No transactions found in {pdf_path}")
                return {
                    "status": "warning",
                    "message": "No transactions found",
                    "pdf_path": pdf_path
                }
            
            self.logger.info(f"Extracted {len(transactions)} transactions")
            self.log_memory_usage("after transaction extraction")
            
            # Step 3: Create Chunks based on extraction type
            if extraction_type == "summary":
                chunks = self.transaction_extractor.create_spending_summary_chunks(transactions)
                self.logger.info(f"Created {len(chunks)} spending summary chunks")
            else:  # "grouped" or default
                chunks = self.transaction_extractor.create_transaction_chunks(transactions, chunk_size=5)
                self.logger.info(f"Created {len(chunks)} grouped transaction chunks")
            
            if not chunks:
                self.logger.error("No chunks created during transaction chunking")
                return {
                    "status": "error",
                    "message": "No chunks created from transactions",
                    "pdf_path": pdf_path
                }
            
            # Step 4: Add chunk ids for compatibility
            for i, chunk in enumerate(chunks):
                chunk['id'] = chunk.get('id', f"{Path(pdf_path).stem}_chunk_{i}")
                chunk['text'] = chunk.get('content', '')
            
            # Step 5: Generate Embeddings in Batches
            batch_size = self.config.get("embedding_batch_size", 50)
            zero_embedding = [0] * self.config.get('embedding_dimension', 768)
            self.logger.info(f"Starting embedding generation for {len(chunks)} transaction chunks")
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                texts = [chunk['text'] for chunk in batch]
                
                self.logger.info(f"Processing batch {batch_num} with {len(batch)} chunks")
                embeddings = self.embedder.create_embeddings(texts)
                
                success_count = 0
                for chunk, embedding in zip(batch, embeddings):
                    chunk['embedding'] = embedding
                    if embedding and embedding != zero_embedding:
                        success_count += 1
                
                self.logger.info(f"Batch {batch_num}: {success_count}/{len(batch)} successful embeddings")
            
            # Step 6: Store in Pinecone
            valid_chunks = [
                chunk for chunk in chunks
                if chunk.get('embedding') and chunk['embedding'] != zero_embedding
            ]
            
            if not valid_chunks:
                self.logger.error("No valid embeddings created")
                return {
                    "status": "error",
                    "message": "No valid embeddings created",
                    "pdf_path": pdf_path
                }
            
            self.logger.info(f"Storing {len(valid_chunks)} chunks in Pinecone")
            added_count = self.vector_db.add_documents(valid_chunks)
            self.logger.info(f"Stored {added_count} chunks in Pinecone")
            self.log_memory_usage("after storing in Pinecone")
            
            return {
                "status": "success",
                "pdf_path": pdf_path,
                "transactions_extracted": len(transactions),
                "chunks_created": len(chunks),
                "chunks_stored": added_count,
                "extraction_type": extraction_type
            }
        
        except Exception as e:
            self.logger.error(f"Error during transaction extraction: {str(e)}")
            return {
                "status": "error",
                "pdf_path": pdf_path,
                "error": str(e)
            }
    
    def ingest_all_pdfs_with_transactions(self, pdf_directory: str, extraction_type: str = "grouped") -> Dict[str, Any]:
        """
        Ingest all PDFs in a directory with transaction extraction
        
        Args:
            pdf_directory: Path to directory containing PDFs
            extraction_type: Type of extraction - "grouped" or "summary"
        
        Returns:
            Dictionary with aggregated results
        """
        try:
            pdf_dir = Path(pdf_directory)
            pdf_files = list(pdf_dir.glob("*.pdf"))
            
            if not pdf_files:
                self.logger.warning(f"No PDF files found in {pdf_directory}")
                return {
                    "status": "warning",
                    "message": "No PDF files found"
                }
            
            results = {
                "total_files": len(pdf_files),
                "successful": 0,
                "failed": 0,
                "total_transactions": 0,
                "total_chunks": 0,
                "total_stored": 0,
                "files": []
            }
            
            for pdf_file in pdf_files:
                result = self.ingest_pdf_with_transactions(str(pdf_file), extraction_type)
                results["files"].append(result)
                
                if result["status"] == "success":
                    results["successful"] += 1
                    results["total_transactions"] += result.get("transactions_extracted", 0)
                    results["total_chunks"] += result.get("chunks_created", 0)
                    results["total_stored"] += result.get("chunks_stored", 0)
                else:
                    results["failed"] += 1
            
            self.logger.info(f"Transaction extraction completed: {results}")
            return results
        
        except Exception as e:
            self.logger.error(f"Error during batch transaction extraction: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        try:
            self.logger.info(f"Retrieving documents for query: {query[:100]}...")
            
            # Create embedding for query
            query_embedding = self.embedder.create_embedding(
                query,
                task_type="RETRIEVAL_QUERY"
            )
            
            # Search in vector database
            results = self.vector_db.search(query_embedding, top_k=top_k)
            
            self.logger.info(f"Retrieved {len(results)} documents")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during retrieval: {str(e)}")
            return []
    
    def query_and_answer(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Query database and generate answer using Gemini
        """
        try:
            self.logger.info(f"Query & Answer: {question}")
            
            results = self.retrieve(question, top_k=top_k)
            
            if not results:
                return {
                    "question": question,
                    "answer": "No relevant documents found.",
                    "source_chunks": []
                }
            
            context_chunks = [result.get('content') or result.get('text') for result in results]
            answer = self.embedder.generate_answer(question, context_chunks)
            
            return {
                "question": question,
                "answer": answer,
                "source_chunks": results
            }
            
        except Exception as e:
            self.logger.error(f"Error in query_and_answer: {str(e)}")
            return {"question": question, "answer": f"Error: {str(e)}", "source_chunks": []}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        try:
            doc_count = self.vector_db.get_document_count()
            return {
                "total_documents": doc_count,
                "vector_db_path": str(self.config.get('vector_db_path')),
                "collection_name": self.config.get('vector_db_name'),
                "embedding_model": self.config.get('embedding_model')
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return {}
    
    def clear(self):
        """Clear all data from the pipeline"""
        try:
            self.vector_db.delete_all()
            self.logger.info("Pipeline cleared")
        except Exception as e:
            self.logger.error(f"Error clearing pipeline: {str(e)}")
            raise
