"""
Vector Database Module
Handles storage and retrieval of embeddings using Pinecone
"""
import logging
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
import os
import time

logger = logging.getLogger(__name__)


class VectorDatabase:
    """Manage vector storage and retrieval using Pinecone"""
    
    def __init__(self, api_key: str = None, environment: str = None, index_name: str = "rag-documents", embedding_dimension: int = 768):
        """
        Initialize Pinecone vector database
        
        Args:
            api_key: Pinecone API key (uses env variable if not provided)
            environment: Pinecone environment (uses env variable if not provided)
            index_name: Name of the Pinecone index
            embedding_dimension: Dimension of embeddings (default 768)
        """
        self.logger = logging.getLogger(__name__)
        self.index_name = index_name
        self.embedding_dimension = embedding_dimension
        
        # Get credentials from parameters or environment
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        
        if not self.api_key:
            raise ValueError("Pinecone API key not provided. Set PINECONE_API_KEY environment variable.")
        
        try:
            # Initialize Pinecone client with API key
            self.pc = Pinecone(api_key=self.api_key)
            self.logger.info(f"✅ Pinecone client initialized successfully")
            
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes.indexes]
            
            if self.index_name not in index_names:
                self.logger.info(f"📝 Index '{self.index_name}' not found. Creating new index...")
                self._create_index()
                time.sleep(5)  # Wait for index to be ready
                self.logger.info(f"✅ Index '{self.index_name}' created successfully")
            
            # Get the index
            self.index = self.pc.Index(self.index_name)
            
            # Verify index connection
            index_stats = self.index.describe_index_stats()
            total_vectors = index_stats.get('total_vector_count', 0)
            self.logger.info(f"✅ Connected to Pinecone index '{self.index_name}' ({total_vectors} vectors)")
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing Pinecone: {str(e)}")
            raise
    
    def _create_index(self):
        """Create a new Pinecone index with serverless spec"""
        try:
            self.pc.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        except Exception as e:
            self.logger.error(f"❌ Error creating index: {str(e)}")
            raise
    
    def add_documents(self, chunks: List[dict]) -> int:
        """
        Add documents with embeddings to Pinecone
        
        Args:
            chunks: List of chunk dictionaries with 'id', 'text', and 'embedding'
        
        Returns:
            Number of documents added
        """
        if not chunks:
            self.logger.warning("No chunks to add")
            return 0
            
        try:
            vectors = []
            failed_chunks = []
            
            for i, chunk in enumerate(chunks):
                try:
                    # Validate chunk has required fields
                    if 'id' not in chunk:
                        chunk['id'] = f"chunk_{i}"
                    
                    if 'embedding' not in chunk:
                        self.logger.warning(f"Chunk {chunk.get('id')} missing embedding, skipping")
                        failed_chunks.append(chunk['id'])
                        continue
                    
                    # Validate embedding dimension
                    embedding = chunk['embedding']
                    if len(embedding) != self.embedding_dimension:
                        self.logger.warning(
                            f"Chunk {chunk['id']} has embedding dimension {len(embedding)}, "
                            f"expected {self.embedding_dimension}. Skipping."
                        )
                        failed_chunks.append(chunk['id'])
                        continue
                    
                    text = chunk.get("text") or chunk.get("content") or ""
                    
                    vectors.append({
                        "id": str(chunk["id"]),
                        "values": embedding,
                        "metadata": {
                            "source": chunk.get("source", "unknown"),
                            "text": text[:1000],  # Limit metadata text size
                            "chunk_index": str(chunk.get("chunk_index", 0))
                        }
                    })
                except Exception as e:
                    self.logger.error(f"Error processing chunk: {str(e)}")
                    failed_chunks.append(chunk.get('id', f'chunk_{i}'))
                    continue
            
            # Upsert vectors in batches
            if vectors:
                batch_size = 100
                total_upserted = 0
                
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i+batch_size]
                    try:
                        upsert_response = self.index.upsert(vectors=batch)
                        upserted = upsert_response.get('upserted_count', len(batch))
                        total_upserted += upserted
                        self.logger.info(f"✅ Upserted {upserted} vectors (batch {i//batch_size + 1})")
                    except Exception as e:
                        self.logger.error(f"Error upserting batch: {str(e)}")
                
                self.logger.info(f"✅ Successfully added {total_upserted} documents to Pinecone")
                
                if failed_chunks:
                    self.logger.warning(f"⚠️  Failed to process {len(failed_chunks)} chunks")
                
                return total_upserted
            else:
                self.logger.warning("No valid vectors to upsert")
                return 0
                
        except Exception as e:
            self.logger.error(f"❌ Error adding documents to Pinecone: {str(e)}")
            return 0
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents using embedding in Pinecone
        
        Args:
            query_embedding: Embedding vector of the query
            top_k: Number of results to return
            
        Returns:
            List of similar documents
        """
        try:
            # Validate query embedding dimension
            if len(query_embedding) != self.embedding_dimension:
                self.logger.warning(
                    f"Query embedding dimension {len(query_embedding)}, "
                    f"expected {self.embedding_dimension}. Padding/truncating..."
                )
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Format results
            documents = []
            if results and 'matches' in results:
                for match in results['matches']:
                    documents.append({
                        'id': match['id'],
                        'text': match['metadata'].get('text', ''),
                        'content': match['metadata'].get('text', ''),  # Both for compatibility
                        'metadata': {
                            'source': match['metadata'].get('source', 'unknown'),
                            'chunk_index': match['metadata'].get('chunk_index', '0')
                        },
                        'score': match['score']  # Similarity score (0-1 for cosine distance)
                    })
            
            self.logger.info(f"✅ Found {len(documents)} similar documents (top_k={top_k})")
            return documents
            
        except Exception as e:
            self.logger.error(f"❌ Error searching documents: {str(e)}")
            return []
    
    def get_document_count(self) -> int:
        """Get total number of vectors in Pinecone index"""
        try:
            stats = self.index.describe_index_stats()
            count = stats['total_vector_count']
            return count
        except Exception as e:
            self.logger.error(f"Error getting document count: {str(e)}")
            return 0
    
    def delete_all(self):
        """Delete all vectors from Pinecone index"""
        try:
            # Delete all vectors by querying and deleting
            self.index.delete(delete_all=True)
            self.logger.info("All documents deleted from Pinecone index")
        except Exception as e:
            self.logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Retrieve all document metadata from Pinecone index"""
        try:
            # Get index stats to see how many vectors exist
            stats = self.index.describe_index_stats()
            total_vectors = stats.get('total_vector_count', 0)
            
            self.logger.info(f"Total vectors in index: {total_vectors}")
            
            if total_vectors == 0:
                self.logger.warning("No vectors found in Pinecone index")
                return []
            
            documents = []
            
            # Use list_sparse to get all vectors (works better with Pinecone's API)
            # Alternatively, fetch vectors in batches using a query
            try:
                # Try to list vector IDs
                list_response = self.index.list(limit=1000)
                vector_ids = [item for item in list_response]
                
                self.logger.info(f"Found {len(vector_ids)} vectors to fetch")
                
                if vector_ids:
                    # Fetch all vectors with their metadata
                    fetch_response = self.index.fetch(ids=vector_ids[:1000])  # Fetch max 1000 at a time
                    
                    if fetch_response and 'vectors' in fetch_response:
                        for vid, vdata in fetch_response['vectors'].items():
                            if 'metadata' in vdata:
                                documents.append({
                                    'id': vid,
                                    'content': vdata['metadata'].get('content', ''),
                                    'text': vdata['metadata'].get('content', ''),
                                    'metadata': {
                                        'source': vdata['metadata'].get('source', 'unknown'),
                                        'chunk_index': vdata['metadata'].get('chunk_index', 0)
                                    }
                                })
                    
                    self.logger.info(f"Successfully retrieved {len(documents)} documents")
            except Exception as list_err:
                self.logger.warning(f"Error using list/fetch approach: {str(list_err)}")
                # Fallback: Use a query-based approach to fetch documents
                # This ensures we get at least some documents if they exist
                try:
                    import numpy as np
                    # Create a zero vector query to get similar documents
                    zero_vector = [0.0] * self.embedding_dimension
                    query_results = self.index.query(
                        vector=zero_vector,
                        top_k=min(100, total_vectors),
                        include_metadata=True
                    )
                    
                    if query_results and 'matches' in query_results:
                        seen_ids = set()
                        for match in query_results['matches']:
                            vid = match.get('id')
                            if vid and vid not in seen_ids:
                                seen_ids.add(vid)
                                documents.append({
                                    'id': vid,
                                    'content': match.get('metadata', {}).get('content', ''),
                                    'text': match.get('metadata', {}).get('content', ''),
                                    'metadata': {
                                        'source': match.get('metadata', {}).get('source', 'unknown'),
                                        'chunk_index': match.get('metadata', {}).get('chunk_index', 0)
                                    }
                                })
                        self.logger.info(f"Retrieved {len(documents)} documents via query fallback")
                except Exception as query_err:
                    self.logger.error(f"Error using query fallback: {str(query_err)}")
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error retrieving all documents: {str(e)}")
            return []
