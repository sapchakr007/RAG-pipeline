"""
Fast Text Chunker - Optimized for performance
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class FastTextChunker:
    """Simple, fast chunker without complex sentence boundary logic"""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 75):
        """
        Initialize chunker
        
        Args:
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.logger = logging.getLogger(__name__)
    
    def chunk_text(self, text: str, source: str = "document") -> List[dict]:
        """
        Fast chunking without complex boundary detection
        
        Args:
            text: Text to chunk
            source: Source identifier
            
        Returns:
            List of chunks
        """
        if not text or not isinstance(text, str):
            self.logger.warning("Invalid text provided")
            return []
        
        text = text.strip()
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            # Calculate end position
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) > 0:
                chunks.append({
                    "id": f"{source}_chunk_{chunk_id}",
                    "text": chunk_text,
                    "content": chunk_text,
                    "source": source,
                    "chunk_index": chunk_id,
                    "start_char": start,
                    "end_char": end
                })
                chunk_id += 1
            
            # Move to next chunk - must always advance by at least 1
            start = max(end - self.overlap, start + 1)
            
            # Break if we're at the end
            if end == len(text):
                break
        
        self.logger.info(f"Created {len(chunks)} chunks from {source}")
        return chunks
