# RAG Pipeline - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Setup (One-time)

```bash
# Create virtual environment
python -m venv ainv
source ainv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add your API keys to .env
cp .env.example .env
# Edit .env with your Pinecone & LLM provider keys
```

### Step 2: Ingest PDFs

```bash
# Place your PDFs in data/pdfs/
mkdir -p data/pdfs
cp /path/to/your/pdfs/* data/pdfs/

# Run ingestion
python ingest_optimized.py
```

Expected output:
```
Starting ingestion...
Ingesting PDF: document.pdf
  - Loaded 5000 characters
  - Created 20 chunks
  - Generated embeddings
  - Stored in Pinecone
```

### Step 3: Query

**Option A: Via Web UI (Recommended)**

```bash
# Terminal 1 - Backend API
python -m flask run --port 5001

# Terminal 2 - React Frontend
cd frontend && npm start
# Opens http://localhost:3000
```

**Option B: Via Python Script**

```bash
python example_usage.py
```

**Option C: Via API**

```bash
# Query
curl -X POST http://localhost:5001/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Your question here", "top_k": 3}'

# Health check
curl http://localhost:5001/api/health
```

---

## 📁 Project Structure

```
RAG-pipeline/
├── app.py                    # Flask REST API
├── ingest_optimized.py       # Use this to ingest PDFs ⭐
├── example_usage.py          # Python usage example
├── rag_complete_demo.py      # Full end-to-end demo
├── main.py                   # Main entry point
├── config/
│   └── settings.py           # Configuration
├── src/
│   ├── rag_pipeline.py       # Core pipeline logic
│   ├── pdf_loader.py         # PDF extraction
│   ├── chunker.py            # Text chunking
│   ├── embedder.py           # Embeddings & LLM
│   └── vector_db.py          # Pinecone interface
├── frontend/                 # React UI
├── data/
│   ├── pdfs/                 # Place your PDFs here
│   └── vector_store/         # Local storage
├── tests/                    # Test suite
└── requirements.txt          # Dependencies
```

---

## 🎯 Common Tasks

### Ingest New PDFs
```bash
python ingest_optimized.py
```

### Query via Python
```python
from config.settings import CONFIG
from src.rag_pipeline import RAGPipeline

pipeline = RAGPipeline(config=CONFIG)
result = pipeline.query_and_answer("Your question?", top_k=3)
print(result['answer'])
```

### Check Pipeline Status
```bash
# Health check API
curl http://localhost:5001/api/health

# Or in Python
pipeline = RAGPipeline(config=CONFIG)
stats = pipeline.get_stats()
print(f"Documents in index: {stats['total_documents']}")
```

### Change LLM Provider
Edit `.env`:
```env
LLM_PROVIDER=groq          # or gemini, perplexity
GROQ_API_KEY=your_key_here
```

---

## ⚙️ Configuration

All settings in `config/settings.py`:

```python
CHUNK_SIZE = 256              # Characters per chunk
CHUNK_OVERLAP = 50            # Overlap between chunks
EMBEDDING_BATCH_SIZE = 50     # Chunks per batch
TOP_K_RESULTS = 5             # Results per query
LLM_PROVIDER = "groq"         # gemini, groq, or perplexity
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 5000 already in use | Use port 5001: `python -m flask run --port 5001` |
| "No documents found" | Run `python ingest_optimized.py` first |
| Slow queries | Reduce `TOP_K_RESULTS` in settings |
| API key errors | Check `.env` file has all required keys |
| Import errors | Run `pip install -r requirements.txt` |

---

## 📚 Full Documentation

See [END_TO_END_GUIDE.md](END_TO_END_GUIDE.md) for complete architecture, API reference, and advanced usage.

---

## 🎓 File Reference

| File | Purpose | When to Use |
|------|---------|------------|
| `ingest_optimized.py` | Ingest PDFs with batching | Run once to load documents |
| `app.py` | Flask REST API | Start backend: `python -m flask run` |
| `example_usage.py` | Python example | Learn how to use pipeline in code |
| `rag_complete_demo.py` | Full demo with queries | See complete workflow |
| `config/settings.py` | Configuration | Adjust parameters here |
| `src/rag_pipeline.py` | Core logic | Core pipeline implementation |

---

## 🚀 Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Set up `.env` with API keys
3. ✅ Add PDFs to `data/pdfs/`
4. ✅ Run: `python ingest_optimized.py`
5. ✅ Start backend: `python -m flask run --port 5001`
6. ✅ Start frontend: `cd frontend && npm start`
7. ✅ Open http://localhost:3000 and start querying!

