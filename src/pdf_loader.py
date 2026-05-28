"""
PDF Loader Module
Handles extraction of text from PDF files
"""
import logging
from pathlib import Path
from typing import List, Dict
import PyPDF2

logger = logging.getLogger(__name__)


class PDFLoader:
    """Load and extract text from PDF files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_pdf(self, pdf_path: str) -> str:
        """
        Load a PDF file and extract all text
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            if pdf_path.suffix.lower() != ".pdf":
                raise ValueError(f"File is not a PDF: {pdf_path}")
            
            text = ""
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                self.logger.info(f"Loading PDF with {num_pages} pages: {pdf_path.name}")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text += page.extract_text()
                    if (page_num + 1) % 10 == 0:
                        self.logger.info(f"Processed {page_num + 1}/{num_pages} pages")
            
            self.logger.info(f"Successfully loaded PDF: {pdf_path.name}")
            return text
            
        except Exception as e:
            self.logger.error(f"Error loading PDF {pdf_path}: {str(e)}")
            raise
    
    def load_multiple_pdfs(self, pdf_dir: str) -> Dict[str, str]:
        """
        Load multiple PDF files from a directory
        
        Args:
            pdf_dir: Directory containing PDF files
            
        Returns:
            Dictionary with filename as key and extracted text as value
        """
        pdf_dir = Path(pdf_dir)
        if not pdf_dir.exists():
            raise FileNotFoundError(f"Directory not found: {pdf_dir}")
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {pdf_dir}")
            return {}
        
        documents = {}
        for pdf_file in pdf_files:
            try:
                documents[pdf_file.name] = self.load_pdf(str(pdf_file))
            except Exception as e:
                self.logger.error(f"Failed to load {pdf_file.name}: {str(e)}")
                continue
        
        self.logger.info(f"Loaded {len(documents)}/{len(pdf_files)} PDF files")
        return documents
