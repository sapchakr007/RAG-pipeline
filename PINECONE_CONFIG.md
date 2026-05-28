# Pinecone Configuration Guide

## Overview

This guide explains how to configure and use Pinecone as your vector database for the RAG pipeline.

## Setup Steps

### 1. Get Your Pinecone API Key

1. Go to [Pinecone Console](https://app.pinecone.io)
2. Sign up or log in with your account
3. Navigate to **API Keys** section
4. Copy your API key
5. Update your `.env` file or `config/settings.py` with:

```env
PINECONE_API_KEY=your_api_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-documents
```

### 2. Configuration in Code

The configuration is managed in `config/settings.py`:

```python
# Pinecone Configuration
PINECONE_API_KEY = os.getenv(
    "PINECONE_API_KEY",
    "your_default_api_key_here"  # Replace with your actual key
)
PINECONE_ENVIRONMENT = os.getenv(
    "PINECONE_ENVIRONMENT",
    "us-east-1"
)
PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "rag-documents"
)
```

### 3. Index Creation

The RAG pipeline **automatically creates** the Pinecone index if it doesn't exist. The following settings are used:

- **Metric**: `cosine` (for semantic similarity)
- **Dimension**: 768 (default for most embeddings)
- **Type**: Serverless on AWS us-east-1

To customize these, edit `src/vector_db.py`:

```python
self.pc.create_index(
    name=self.index_name,
    dimension=self.embedding_dimension,
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    )
)
```

## Testing Your Configuration

Run the test script to verify your Pinecone setup:

```bash
python test_pinecone_config.py
```

This will:
- ✅ Test API connection
- ✅ List available indexes
- ✅ Check index status
- ✅ Test embedding generation

## Using Pinecone with the RAG Pipeline

### Ingesting PDFs

```python
from src.rag_pipeline import RAGPipeline
from config.settings import CONFIG

# Initialize pipeline
pipeline = RAGPipeline(CONFIG)

# Process PDFs from data/pdfs/
pipeline.ingest_pdfs("data/pdfs/")
```

### Searching for Similar Documents

```python
# Generate query embedding
query_text = "Your search query"
query_embedding = pipeline.embedder.embed_text(query_text)

# Search Pinecone
results = pipeline.vector_db.search(
    query_embedding=query_embedding,
    top_k=5  # Get top 5 results
)

for result in results:
    print(f"Document: {result['text']}")
    print(f"Similarity Score: {result['score']}")
```

## Troubleshooting

### Error: "Pinecone API key not provided"

**Solution**: Make sure your API key is set in:
1. `.env` file with `PINECONE_API_KEY=...`
2. Or directly in `config/settings.py`
3. Or passed to `VectorDatabase()` constructor

### Error: "Index not found"

**Solution**: The index will be automatically created on first ingestion. If you need to manually create it:

```python
from src.vector_db import VectorDatabase

vdb = VectorDatabase(
    api_key="your_api_key",
    index_name="rag-documents"
)
```

### Error: "Embedding dimension mismatch"

**Solution**: Ensure your embedding dimension matches your embedder:
- Gemini: 768
- Groq: varies (check output)
- Perplexity: varies (check output)

Update in `config/settings.py`:
```python
EMBEDDING_DIMENSION = 768  # Match your embedder
```

### Slow Ingestion

**Optimization Tips**:
1. Use batch processing (already implemented)
2. Reduce chunk size in `config/settings.py`
3. Use serverless indexes for better scaling

## Pinecone API Reference

### Creating Index

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="your_api_key")
pc.create_index(
    name="my-index",
    dimension=768,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
```

### Upserting Vectors

```python
index = pc.Index("my-index")
index.upsert(vectors=[
    {
        "id": "chunk_1",
        "values": [0.1, 0.2, ..., 0.768],
        "metadata": {"source": "document.pdf", "text": "..."}
    }
])
```

### Querying

```python
results = index.query(
    vector=[0.1, 0.2, ..., 0.768],
    top_k=5,
    include_metadata=True
)
```

### Listing Indexes

```python
indexes = pc.list_indexes()
for idx in indexes.indexes:
    print(idx.name)
```

## Environment Variables

Add to your `.env` file:

```env
# Pinecone Configuration
PINECONE_API_KEY=pcsk_xxxxxx
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-documents

# Gemini Configuration (for embeddings)
GEMINI_API_KEY=AIzaSyC2OUGzujkOhkBMZmbXfMjNGw3SGx2fVpM
GEMINI_MODEL=gemini-embedding-001
EMBEDDING_DIMENSION=768

# LLM Provider
LLM_PROVIDER=gemini  # Options: gemini, groq, perplexity
```

## Advanced Configuration

### Custom Embedding Dimension

If using a different embedding model with non-768 dimensions:

```python
# In config/settings.py
EMBEDDING_DIMENSION = 1536  # Or your embedder's dimension

# In rag_pipeline.py
self.vector_db = VectorDatabase(
    api_key=config.get('pinecone_api_key'),
    index_name=config.get('vector_db_name', 'rag-documents'),
    embedding_dimension=1536  # Match this
)
```

### Using Different Cloud Regions

```python
# In src/vector_db.py
spec=ServerlessSpec(
    cloud="gcp",  # Options: aws, gcp, azure
    region="us-central1"  # Your region
)
```

### Updating Index Metrics

If you need to change the distance metric (cosine, euclidean, dotproduct):

```python
# Delete and recreate index with new metric
pc.delete_index("old-index")
pc.create_index(
    name="new-index",
    dimension=768,
    metric="euclidean",  # Or your preferred metric
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
```

## Performance Tips

1. **Batch Upserts**: Already implemented (100 vectors per batch)
2. **Metadata Compression**: Text is limited to 1000 chars
3. **Index Scaling**: Serverless indexes auto-scale with demand
4. **Query Optimization**: Use appropriate `top_k` values

## Resources

- [Pinecone Documentation](https://docs.pinecone.io)
- [Pinecone Python SDK](https://docs.pinecone.io/reference/python/latest/)
- [Serverless Indexes](https://docs.pinecone.io/guides/indexes/serverless-indexes)
