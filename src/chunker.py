"""
Text Chunker Module
Handles splitting of text into manageable chunks for embedding
"""
import logging
from typing import List
import re

logger = logging.getLogger(__name__)


class TextChunker:
    """Split text into overlapping chunks"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize chunker
        
        Args:
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.logger = logging.getLogger(__name__)
    
    def chunk_text(self, text: str, source: str = "document") -> List[dict]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            source: Source identifier for the text
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        self.logger.info(f"Starting chunking for text with {len(text)} characters from {source}")
        
        if not text or not isinstance(text, str):
            self.logger.warning("Invalid text provided for chunking")
            return []
        
        # Clean text
        self.logger.info("Cleaning text...")
        text = self._clean_text(text)
        self.logger.info(f"Text cleaned. Length after cleaning: {len(text)} characters")
        
        chunks = []
        start = 0
        chunk_id = 0
        self.logger.info(f"Starting chunking loop. Total text length: {len(text)} characters")
        
        while start < len(text):
            # Calculate end position
            end = min(start + self.chunk_size, len(text))
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending (. ? !) within the last 100 characters
                window = text[max(start, end - 100):end]
                last_boundary = -1
                for char in ['.', '?', '!']:
                    idx = window.rfind(char)
                    if idx > last_boundary:
                        last_boundary = idx
                
                if last_boundary != -1:
                    # Convert window-relative index to absolute text index
                    end = max(start, end - 100) + last_boundary + 1
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if chunk_text:
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

            next_start = end - self.overlap
            if next_start <= start:
                next_start = end

            if end == len(text):
                break

            start = next_start

        self.logger.info(f"Created {len(chunks)} chunks from {source}")
        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Clean text by normalizing whitespace.
        """
        # Remove multiple spaces/tabs but preserve newlines
        text = re.sub(r'[ \t]+', ' ', text)
        # Normalize multiple consecutive newlines to a single newline
        text = re.sub(r'\n+', '\n', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def chunk_multiple_texts(self, texts: dict) -> List[dict]:
        """
        Chunk multiple texts from different sources
        
        Args:
            texts: Dictionary with source names as keys and text as values
            
        Returns:
            Combined list of chunks from all sources
        """
        all_chunks = []
        for source, text in texts.items():
            chunks = self.chunk_text(text, source)
            all_chunks.extend(chunks)
        
        self.logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks
