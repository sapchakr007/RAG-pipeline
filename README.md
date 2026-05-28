# RAG Pipeline - Retrieval Augmented Generation

A complete end-to-end RAG (Retrieval-Augmented Generation) pipeline that extracts text from PDFs, chunks them, creates embeddings using Google's Gemini API, and stores them in a vector database for semantic search and retrieval.

## Features

- **PDF Text Extraction**: Load and extract text from PDF files
- **Intelligent Chunking**: Split documents into overlapping chunks with smart sentence boundary detection
- **Google Gemini Embeddings**: Create embeddings using Google's generative AI API
- **Vector Database**: Store and retrieve embeddings using ChromaDB with persistent storage
- **Semantic Search**: Find relevant documents based on semantic similarity
- **Batch Processing**: Ingest multiple PDFs with error handling

## Project Structure

```
RAG-pipeline/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── pdf_loader.py            # PDF text extraction
│   ├── chunker.py               # Text chunking logic
│   ├── embedder.py              # Gemini API embedding creation
│   ├── vector_db.py             # ChromaDB vector database management
│   └── rag_pipeline.py          # Main pipeline orchestration
├── config/
│   └── settings.py              # Configuration settings
├── data/
│   ├── pdfs/                    # Input PDF files directory
│   └── vector_store/            # ChromaDB persistent storage
├── tests/                       # Unit tests directory
├── main.py                      # Entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Installation

### Prerequisites
- Python 3.8+
- Google Generative AI API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Setup

1. **Clone the repository**
   ```bash
   cd RAG-pipeline
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Gemini API key (already provided in the example)

## Usage

### Basic Usage

1. **Place PDFs in the data folder**
   ```bash
   cp your_document.pdf data/pdfs/
   ```

2. **Run the pipeline**
   ```bash
   python main.py
   ```

### Python API Usage

```python
from config.settings import (
    GEMINI_API_KEY, GEMINI_MODEL, PDF_DIR, 
    VECTOR_STORE_DIR, CHUNK_SIZE, CHUNK_OVERLAP
)
from src.rag_pipeline import RAGPipeline

# Initialize pipeline
config = {
    'gemini_api_key': GEMINI_API_KEY,
    'embedding_model': GEMINI_MODEL,
    'vector_db_path': str(VECTOR_STORE_DIR),
    'chunk_size': CHUNK_SIZE,
    'chunk_overlap': CHUNK_OVERLAP
}

pipeline = RAGPipeline(config)

# Ingest a single PDF
result = pipeline.ingest_pdf('path/to/document.pdf')
print(f"Ingestion result: {result}")

# Or ingest multiple PDFs from a directory
results = pipeline.ingest_multiple_pdfs('data/pdfs')
print(f"Batch results: {results}")

# Retrieve relevant documents
query = "What is machine learning?"
results = pipeline.retrieve(query, top_k=5)

for i, result in enumerate(results, 1):
    print(f"Result {i}:")
    print(f"  Content: {result['content'][:200]}...")
    print(f"  Source: {result['metadata']['source']}")
    print()

# Get pipeline statistics
stats = pipeline.get_stats()
print(f"Total documents: {stats['total_documents']}")
```

## Components

### 1. PDF Loader (`pdf_loader.py`)
Extracts text from PDF files using PyPDF2.

**Key Methods:**
- `load_pdf(pdf_path)`: Load a single PDF
- `load_multiple_pdfs(pdf_dir)`: Load multiple PDFs from a directory

### 2. Text Chunker (`chunker.py`)
Splits documents into overlapping chunks with intelligent boundary detection.

**Key Methods:**
- `chunk_text(text, source)`: Chunk a single text
- `chunk_multiple_texts(texts)`: Chunk multiple texts

### 3. Embedder (`embedder.py`)
Creates embeddings using Google's Gemini API.

**Key Methods:**
- `create_embedding(text, task_type)`: Create embedding for single text
- `create_embeddings_batch(texts)`: Create embeddings for multiple texts
- `embed_chunks(chunks)`: Add embeddings to chunks

### 4. Vector Database (`vector_db.py`)
Stores and retrieves embeddings using ChromaDB.

**Key Methods:**
- `add_documents(chunks)`: Store documents in vector database
- `search(query_embedding, top_k)`: Search for similar documents
- `get_document_count()`: Get total number of stored documents
- `get_all_documents()`: Retrieve all documents

### 5. RAG Pipeline (`rag_pipeline.py`)
Orchestrates the entire pipeline workflow.

**Key Methods:**
- `ingest_pdf(pdf_path)`: Complete ingestion for a single PDF
- `ingest_multiple_pdfs(pdf_directory)`: Batch ingestion
- `retrieve(query, top_k)`: Query and retrieve relevant documents
- `get_stats()`: Get pipeline statistics
- `clear()`: Clear all data

## Configuration

Edit `config/settings.py` to customize:

- **CHUNK_SIZE**: Characters per chunk (default: 1000)
- **CHUNK_OVERLAP**: Overlap between chunks (default: 200)
- **TOP_K_RESULTS**: Number of search results (default: 5)
- **GEMINI_API_KEY**: Your Google API key
- **VECTOR_DB_TYPE**: Database type (currently ChromaDB)

## API Keys

The pipeline uses your provided Gemini API key:
```
AIzaSyC2OUGzujkOhkBMZmbXfMjNGw3SGx2fVpM
```

This is already configured in the settings.

## Output

### Ingestion Results
```json
{
  "status": "success",
  "pdf_file": "document.pdf",
  "total_chunks": 15,
  "documents_stored": 15,
  "text_length": 25000
}
```

### Retrieval Results
```json
{
  "id": "source_chunk_0",
  "content": "Extracted chunk content...",
  "metadata": {
    "source": "document",
    "chunk_index": "0"
  },
  "distance": 0.15
}
```

## Error Handling

The pipeline includes comprehensive error handling:
- Invalid PDF file detection
- Missing API key handling
- Rate limiting for API calls
- Failed chunk validation
- Graceful degradation for failed operations

## Logging

Logs are output to the console with the following levels:
- **INFO**: Normal operations
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors

Configure log level in `config/settings.py` (LOG_LEVEL).

## Requirements

See `requirements.txt` for full dependencies:
- PyPDF2: PDF text extraction
- google-generativeai: Gemini API integration
- chromadb: Vector database
- python-dotenv: Environment variable management
- numpy: Numerical operations
- pydantic: Data validation

## Troubleshooting

### API Key Issues
- Verify your API key is valid
- Check that the key is properly set in `.env` or `config/settings.py`
- Ensure the API is enabled in Google Cloud Console

### PDF Processing Issues
- Ensure PDFs are not encrypted
- Check file permissions
- Verify PDF format is standard

### Embedding Errors
- Check rate limits (add delays between requests)
- Verify text is not too long
- Ensure stable internet connection

## Future Enhancements

- [ ] Support for multiple vector databases (Pinecone, Weaviate)
- [ ] Advanced document pre-processing
- [ ] Query expansion and refinement
- [ ] Caching for frequently accessed embeddings
- [ ] Integration with LLMs for answer generation
- [ ] Web interface for document management
- [ ] REST API endpoints
- [ ] Multi-language support

## License

MIT License

## Author

Created for RAG Pipeline demonstration

## Support

For issues or questions, please open an issue in the repository.