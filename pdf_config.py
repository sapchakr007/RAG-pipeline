"""
PDF Ingestion Configuration
Specifies which PDFs to exclude from processing
"""

# List of PDFs to exclude from ingestion
# Add PDF names here if you don't want them to be processed
EXCLUDED_PDFS = [
    # "kotak.pdf"  # Uncomment to exclude kotak.pdf
]

# Extraction type for new PDFs: "grouped" or "summary"
DEFAULT_EXTRACTION_TYPE = "grouped"

# Number of transactions per chunk (for grouped extraction)
CHUNK_SIZE = 5

# Query settings
TOP_K_RESULTS = 5  # Number of relevant chunks to retrieve for queries
