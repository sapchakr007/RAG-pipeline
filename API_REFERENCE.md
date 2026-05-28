# RAG Pipeline - API Reference

Complete API documentation for all classes and methods in the RAG Pipeline.

## Table of Contents
1. [RAGPipeline](#ragpipeline)
2. [PDFLoader](#pdfloader)
3. [TextChunker](#textchunker)
4. [GeminiEmbedder](#geminiembedder)
5. [VectorDatabase](#vectordatabase)

---

## RAGPipeline

Main orchestration class that manages the entire RAG pipeline workflow.

### Initialization

```python
from src.rag_pipeline import RAGPipeline

config = {
    'gemini_api_key': 'AIzaSyC2OUGzujkOhkBMZmbXfMjNGw3SGx2fVpM',
    'embedding_model': 'models/embedding-001',
    'vector_db_path': './data/vector_store',
    'vector_db_name': 'rag_documents',
    'chunk_size': 1000,
    'chunk_overlap': 200
}

pipeline = RAGPipeline(config)
```

### Methods

#### `ingest_pdf(pdf_path: str) -> Dict[str, Any]`

Ingest a single PDF file into the pipeline.

**Parameters:**
- `pdf_path` (str): Path to the PDF file

**Returns:**
```python
{
    "status": "success",  # or "error"
    "pdf_file": "document.pdf",
    "total_chunks": 15,
    "documents_stored": 15,
    "text_length": 25000  # characters
}
```

**Example:**
```python
result = pipeline.ingest_pdf('data/pdfs/document.pdf')
if result['status'] == 'success':
    print(f"Created {result['total_chunks']} chunks")
```

#### `ingest_multiple_pdfs(pdf_directory: str) -> Dict[str, Any]`

Ingest multiple PDF files from a directory.

**Parameters:**
- `pdf_directory` (str): Path to directory containing PDFs

**Returns:**
```python
{
    "total_files": 5,
    "successful": 4,
    "failed": 1,
    "total_chunks": 75,
    "total_stored": 74,
    "files": [
        {
            "status": "success",
            "pdf_file": "doc1.pdf",
            "total_chunks": 15,
            "documents_stored": 15
        }
    ]
}
```

**Example:**
```python
results = pipeline.ingest_multiple_pdfs('data/pdfs')
print(f"Ingested {results['successful']} of {results['total_files']} PDFs")
```

#### `retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]`

Retrieve relevant documents for a query using semantic search.

**Parameters:**
- `query` (str): The search query
- `top_k` (int): Number of results to return (default: 5)

**Returns:**
```python
[
    {
        "id": "document_chunk_0",
        "content": "Extracted chunk content...",
        "metadata": {
            "source": "document.pdf",
            "chunk_index": "0"
        },
        "distance": 0.15  # Lower is more similar
    }
]
```

**Example:**
```python
results = pipeline.retrieve("What is machine learning?", top_k=3)
for result in results:
    print(f"Source: {result['metadata']['source']}")
    print(f"Content: {result['content'][:200]}...")
```

#### `get_stats() -> Dict[str, Any]`

Get pipeline statistics.

**Returns:**
```python
{
    "total_documents": 150,
    "vector_db_path": "/path/to/vector_store",
    "collection_name": "rag_documents",
    "embedding_model": "models/embedding-001"
}
```

**Example:**
```python
stats = pipeline.get_stats()
print(f"Total documents: {stats['total_documents']}")
```

#### `clear()`

Delete all documents from the vector database.

**Example:**
```python
pipeline.clear()  # Reset the database
```

---

## PDFLoader

Handles PDF text extraction.

### Initialization

```python
from src.pdf_loader import PDFLoader

loader = PDFLoader()
```

### Methods

#### `load_pdf(pdf_path: str) -> str`

Load a single PDF and extract all text.

**Parameters:**
- `pdf_path` (str): Path to the PDF file

**Returns:**
- (str): Extracted text from the PDF

**Raises:**
- `FileNotFoundError`: If PDF file doesn't exist
- `ValueError`: If file is not a PDF

**Example:**
```python
text = loader.load_pdf('document.pdf')
print(f"Extracted {len(text)} characters")
```

#### `load_multiple_pdfs(pdf_dir: str) -> Dict[str, str]`

Load multiple PDFs from a directory.

**Parameters:**
- `pdf_dir` (str): Path to directory containing PDFs

**Returns:**
- (Dict[str, str]): Dictionary with filenames as keys and extracted text as values

**Example:**
```python
documents = loader.load_multiple_pdfs('data/pdfs')
for filename, text in documents.items():
    print(f"{filename}: {len(text)} characters")
```

---

## TextChunker

Handles text splitting into overlapping chunks.

### Initialization

```python
from src.chunker import TextChunker

chunker = TextChunker(chunk_size=1000, overlap=200)
```

**Parameters:**
- `chunk_size` (int): Characters per chunk (default: 1000)
- `overlap` (int): Overlap between chunks (default: 200)

### Methods

#### `chunk_text(text: str, source: str = "document") -> List[dict]`

Split text into overlapping chunks.

**Parameters:**
- `text` (str): Text to chunk
- `source` (str): Source identifier (default: "document")

**Returns:**
```python
[
    {
        "id": "source_chunk_0",
        "content": "First chunk content...",
        "source": "source",
        "chunk_index": 0,
        "start_char": 0,
        "end_char": 1000
    }
]
```

**Example:**
```python
chunks = chunker.chunk_text("Long document text...", source="readme.txt")
print(f"Created {len(chunks)} chunks")
```

#### `chunk_multiple_texts(texts: dict) -> List[dict]`

Chunk multiple texts from different sources.

**Parameters:**
- `texts` (dict): Dictionary with source names and text

**Returns:**
- (List[dict]): Combined list of chunks from all sources

**Example:**
```python
texts = {
    'doc1.pdf': 'content1...',
    'doc2.pdf': 'content2...'
}
all_chunks = chunker.chunk_multiple_texts(texts)
```

---

## GeminiEmbedder

Creates embeddings using Google's Generative AI API.

### Initialization

```python
from src.embedder import GeminiEmbedder

embedder = GeminiEmbedder(
    api_key='AIzaSyC2OUGzujkOhkBMZmbXfMjNGw3SGx2fVpM',
    model='models/embedding-001'
)
```

**Parameters:**
- `api_key` (str): Google Generative AI API key
- `model` (str): Embedding model name (default: 'models/embedding-001')

### Methods

#### `create_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]`

Create embedding for a single text.

**Parameters:**
- `text` (str): Text to embed (will be truncated to 10,000 chars)
- `task_type` (str): Task type - "RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY", etc.

**Returns:**
- (List[float]): 768-dimensional embedding vector

**Example:**
```python
embedding = embedder.create_embedding(
    "Machine learning is...",
    task_type="RETRIEVAL_DOCUMENT"
)
print(f"Embedding dimensions: {len(embedding)}")
```

#### `create_embeddings_batch(texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT", batch_size: int = 10) -> List[dict]`

Create embeddings for multiple texts with rate limiting.

**Parameters:**
- `texts` (List[str]): Texts to embed
- `task_type` (str): Task type (default: "RETRIEVAL_DOCUMENT")
- `batch_size` (int): Batch size for rate limiting (default: 10)

**Returns:**
```python
[
    {
        "text": "First 100 chars...",
        "embedding": [0.1, 0.2, ...],  # 768-dim vector
        "original_text": "Full original text..."
    }
]
```

**Example:**
```python
texts = ["text1", "text2", "text3"]
embeddings = embedder.create_embeddings_batch(texts)
```

#### `embed_chunks(chunks: List[dict]) -> List[dict]`

Add embeddings to document chunks.

**Parameters:**
- `chunks` (List[dict]): Chunks with 'content' key

**Returns:**
- (List[dict]): Chunks with added 'embedding' key

**Example:**
```python
chunks_with_embeddings = embedder.embed_chunks(chunks)
```

---

## VectorDatabase

Manages vector storage and retrieval using ChromaDB.

### Initialization

```python
from src.vector_db import VectorDatabase

db = VectorDatabase(
    db_path='./data/vector_store',
    collection_name='rag_documents'
)
```

**Parameters:**
- `db_path` (str): Path for ChromaDB storage
- `collection_name` (str): Collection name (default: 'rag_documents')

### Methods

#### `add_documents(chunks: List[dict]) -> int`

Store documents with embeddings in the vector database.

**Parameters:**
- `chunks` (List[dict]): Chunks with 'id', 'content', 'embedding' keys

**Returns:**
- (int): Number of documents added

**Example:**
```python
num_stored = db.add_documents(chunks_with_embeddings)
print(f"Stored {num_stored} documents")
```

#### `search(query_embedding: List[float], top_k: int = 5) -> List[Dict]`

Search for similar documents using embedding.

**Parameters:**
- `query_embedding` (List[float]): 768-dimensional query embedding
- `top_k` (int): Number of results (default: 5)

**Returns:**
```python
[
    {
        "id": "document_chunk_0",
        "content": "Retrieved chunk text...",
        "metadata": {"source": "doc.pdf"},
        "distance": 0.15
    }
]
```

**Example:**
```python
results = db.search(query_embedding, top_k=5)
```

#### `get_document_count() -> int`

Get total number of documents in collection.

**Returns:**
- (int): Document count

**Example:**
```python
count = db.get_document_count()
print(f"Total documents: {count}")
```

#### `get_all_documents() -> List[Dict]`

Retrieve all documents from collection.

**Returns:**
```python
[
    {
        "id": "chunk_id",
        "content": "chunk content",
        "metadata": {...}
    }
]
```

**Example:**
```python
all_docs = db.get_all_documents()
```

#### `delete_all()`

Delete all documents from collection.

**Example:**
```python
db.delete_all()  # Clear the database
```

---

## Configuration

Settings are defined in `config/settings.py`:

```python
from config.settings import (
    GEMINI_API_KEY,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_RESULTS,
    PDF_DIR,
    VECTOR_STORE_DIR
)
```

---

## Error Handling

All components include comprehensive error handling:

```python
try:
    result = pipeline.ingest_pdf('document.pdf')
except FileNotFoundError:
    print("PDF file not found")
except Exception as e:
    print(f"Error: {str(e)}")
```

---

## Logging

Enable detailed logging:

```python
import logging

# Set to DEBUG for detailed output
logging.basicConfig(level=logging.DEBUG)
```

Log levels in `config/settings.py`:
- `DEBUG`: Detailed operation traces
- `INFO`: Normal operations (default)
- `WARNING`: Important warnings
- `ERROR`: Errors only
- `CRITICAL`: Critical errors only

---

## Performance Tips

1. **Faster Ingestion:**
   - Reduce CHUNK_SIZE
   - Increase batch_size in embedder

2. **Better Retrieval:**
   - Increase TOP_K_RESULTS
   - Lower SIMILARITY_THRESHOLD

3. **Lower Memory:**
   - Reduce CHUNK_SIZE
   - Use separate vector stores

4. **Batch Operations:**
   - Use `ingest_multiple_pdfs()` instead of individual calls
   - Use `create_embeddings_batch()` for multiple texts

---

For more information, see:
- [README.md](README.md) - Main documentation
- [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - Configuration details
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
