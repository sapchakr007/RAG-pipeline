# Quick Start: Pinecone Setup for RAG Pipeline

## 🚀 5-Minute Setup

### Step 1: Get Pinecone API Key
1. Go to https://app.pinecone.io
2. Sign up/login
3. Get your API key from **API Keys** section
4. Copy the key

### Step 2: Update Configuration

Choose ONE of these options:

**Option A: Using `.env` file (Recommended)**
```bash
echo "PINECONE_API_KEY=pcsk_your_key_here" >> .env
echo "PINECONE_ENVIRONMENT=us-east-1" >> .env
echo "PINECONE_INDEX_NAME=rag-documents" >> .env
```

**Option B: Update `config/settings.py`**
```python
PINECONE_API_KEY = "pcsk_your_key_here"
PINECONE_ENVIRONMENT = "us-east-1"
PINECONE_INDEX_NAME = "rag-documents"
```

### Step 3: Test Connection
```bash
python test_pinecone_config.py
```

Expected output:
```
✅ Connected to Pinecone
✅ Generated embedding with 768 dimensions
✅ All tests passed!
```

### Step 4: Ingest PDFs
```bash
python ingest_transactions.py
```

## 📋 Configuration Files

### Core Configuration
- **Location**: `config/settings.py`
- **What it does**: Sets API keys, models, chunk sizes
- **Key variables**:
  - `PINECONE_API_KEY`: Your Pinecone API key
  - `PINECONE_INDEX_NAME`: Index name (default: "rag-documents")
  - `EMBEDDING_DIMENSION`: Usually 768
  - `LLM_PROVIDER`: "gemini", "groq", or "perplexity"

### Vector Database Module
- **Location**: `src/vector_db.py`
- **Class**: `VectorDatabase`
- **Methods**:
  - `add_documents()`: Add chunks to Pinecone
  - `search()`: Search for similar documents
  - `get_document_count()`: Get vector count
  - `delete_all()`: Clear index

### Embedder
- **Location**: `src/embedder.py`
- **Providers**: GeminiEmbedder, GroqEmbedder, PerplexityEmbedder
- **Method**: `embed_text()` returns embedding vector

## 🔧 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "API key not provided" | Add `PINECONE_API_KEY` to `.env` or `settings.py` |
| "Index not found" | Will be auto-created. Wait 30 seconds. |
| "Dimension mismatch" | Ensure `EMBEDDING_DIMENSION` matches embedder output |
| "Connection timeout" | Check internet & Pinecone API status |
| "Slow ingestion" | Check batch size in `vector_db.py` |

## 📊 Workflow

```
PDF Files
   ↓
PDF Loader → Extract text
   ↓
Chunker → Split into 256-char chunks
   ↓
Embedder → Create 768-dim vectors
   ↓
Vector DB → Store in Pinecone
   ↓
Ready for Queries!
```

## 🧪 Testing

```bash
# Test Pinecone & Embeddings
python test_pinecone_config.py

# Test PDF Ingestion
python ingest_transactions.py

# Test Query
python example_usage.py
```

## 📚 Full Documentation

See [PINECONE_CONFIG.md](PINECONE_CONFIG.md) for detailed configuration options.

## 💡 Tips

1. **First time?** Start with the test script: `python test_pinecone_config.py`
2. **Check index**: Visit https://app.pinecone.io to see your vectors
3. **Monitor usage**: Pinecone free tier = 1M vectors, serverless pay-as-you-go
4. **Batch processing**: Pipeline automatically batches 100 vectors at a time
5. **Error logs**: Check console output for detailed error messages

## 🎯 Next Steps

1. ✅ Configure Pinecone API key
2. ✅ Run test script
3. ✅ Place PDFs in `data/pdfs/`
4. ✅ Run ingestion: `python ingest_transactions.py`
5. ✅ Query results: `python example_usage.py`

## 🆘 Need Help?

1. Check logs for error messages
2. Run `python test_pinecone_config.py` for diagnostics
3. See [PINECONE_CONFIG.md](PINECONE_CONFIG.md) for advanced options
4. Visit [Pinecone Docs](https://docs.pinecone.io)
