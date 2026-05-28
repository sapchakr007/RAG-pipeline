"""
Unit tests for RAG Pipeline components
Run with: python -m pytest tests/
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chunker import TextChunker
from src.pdf_loader import PDFLoader
from src.fast_chunker import FastTextChunker


class TestTextChunker(unittest.TestCase):
    """Test text chunking functionality"""
    
    def setUp(self):
        self.chunker = TextChunker(chunk_size=100, overlap=20)
    
    def test_chunk_text_basic(self):
        """Test basic text chunking"""
        text = "This is a sample document. " * 20
        chunks = self.chunker.chunk_text(text, source="test")
        
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIn('content', chunk)
            self.assertIn('source', chunk)
            self.assertIn('chunk_index', chunk)
    
    def test_chunk_text_empty(self):
        """Test chunking empty text"""
        chunks = self.chunker.chunk_text("", source="empty")
        self.assertEqual(len(chunks), 0)
    
    def test_chunk_text_short(self):
        """Test chunking short text"""
        text = "Short text"
        chunks = self.chunker.chunk_text(text, source="short")
        self.assertGreater(len(chunks), 0)
    
    def test_clean_text(self):
        """Test text cleaning"""
        text = "Multiple    spaces\n\n\nand  newlines"
        cleaned = self.chunker._clean_text(text)
        
        self.assertNotIn("    ", cleaned)
        self.assertNotIn("\n\n", cleaned)

    def test_clean_text_preserves_newlines(self):
        """Test that single newlines are preserved while squashing extra ones"""
        text = "Hello \t world.\n\n\nThis is a new paragraph.\nAnd a new line."
        cleaned = self.chunker._clean_text(text)
        self.assertEqual(cleaned, "Hello world.\nThis is a new paragraph.\nAnd a new line.")
        
    def test_sentence_boundaries_multi_punctuation(self):
        """Test sentence boundaries with ?, ! and ."""
        chunker = TextChunker(chunk_size=30, overlap=5)
        
        # Test question mark splitting
        text_q = "Is this a question? Yes this is a sentence."
        chunks_q = chunker.chunk_text(text_q, source="test")
        self.assertTrue(any(c['content'].endswith('?') for c in chunks_q))
        
        # Test exclamation mark splitting
        text_e = "This is a surprise! Yes this is a sentence."
        chunks_e = chunker.chunk_text(text_e, source="test")
        self.assertTrue(any(c['content'].endswith('!') for c in chunks_e))


class TestFastTextChunker(unittest.TestCase):
    """Test FastTextChunker functionality"""
    
    def setUp(self):
        self.chunker = FastTextChunker(chunk_size=50, overlap=10)
        
    def test_fast_chunk_text_schema(self):
        """Test that FastTextChunker output includes 'text' and 'content'"""
        text = "This is some test text for the fast chunker to chunk."
        chunks = self.chunker.chunk_text(text, source="test")
        
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIn('text', chunk)
            self.assertIn('content', chunk)
            self.assertEqual(chunk['text'], chunk['content'])


class TestPDFLoader(unittest.TestCase):
    """Test PDF loading functionality"""
    
    def setUp(self):
        self.loader = PDFLoader()
    
    def test_load_nonexistent_pdf(self):
        """Test loading non-existent PDF"""
        with self.assertRaises(FileNotFoundError):
            self.loader.load_pdf("nonexistent.pdf")
    
    def test_load_invalid_file(self):
        """Test loading non-PDF file"""
        # Create a temporary non-PDF file
        test_file = Path("/tmp/test.txt")
        test_file.write_text("test content")
        
        try:
            with self.assertRaises(ValueError):
                self.loader.load_pdf(str(test_file))
        finally:
            test_file.unlink()


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_pipeline_initialization(self):
        """Test pipeline can be initialized"""
        from config.settings import (
            GEMINI_API_KEY, GEMINI_MODEL, 
            VECTOR_STORE_DIR, CHUNK_SIZE, CHUNK_OVERLAP
        )
        from src.rag_pipeline import RAGPipeline
        
        config = {
            'gemini_api_key': GEMINI_API_KEY,
            'embedding_model': GEMINI_MODEL,
            'vector_db_path': str(VECTOR_STORE_DIR),
            'chunk_size': CHUNK_SIZE,
            'chunk_overlap': CHUNK_OVERLAP
        }
        
        pipeline = RAGPipeline(config)
        stats = pipeline.get_stats()
        
        self.assertIn('total_documents', stats)
        self.assertIn('vector_db_path', stats)


if __name__ == '__main__':
    unittest.main()
