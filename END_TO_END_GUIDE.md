# RAG Pipeline - Complete End-to-End Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Details](#component-details)
3. [Data Flow](#data-flow)
4. [Ingestion Pipeline](#ingestion-pipeline)
5. [Query Pipeline](#query-pipeline)
6. [API Endpoints](#api-endpoints)
7. [Configuration](#configuration)
8. [Setup Instructions](#setup-instructions)
9. [Usage Examples](#usage-examples)

---

## Architecture Overview

This RAG (Retrieval-Augmented Generation) pipeline is a full-stack application designed to:
- **Ingest** PDF documents and extract text
- **Process** text into manageable chunks with overlapping context
- **Embed** chunks into vector representations using AI models
- **Store** embeddings in Pinecone vector database
- **Retrieve** relevant documents based on semantic similarity
- **Generate** intelligent answers using LLMs

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE (React)                      │
│                   Running on localhost:3000                      │
└────────────────────────────┬──────────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK API BACKEND                             │
│                   Running on localhost:5001                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ • Health Check: /api/health                                 ││
│  │ • Query Handler: /api/query (POST)                          ││
│  │ • Models Info: /api/models (GET)                            ││
│  └─────────────────────────────────────────────────────────────┘│
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RAG PIPELINE ORCHESTRATION                     │
│              (Main pipeline logic and coordination)              │
└────────────────────────────┬──────────────────────────────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌─────────────┐  ┌────────────┐  ┌──────────────┐
    │ PDF Loader  │  │  Chunker   │  │  Embedder    │
    │ (PyPDF2)    │  │(TextChunker)│  │ (Gemini/Groq)│
    └─────────────┘  └────────────┘  └──────────────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Vector Database     │
                  │  (Pinecone Index)    │
                  │ "rag-documents"      │
                  └──────────────────────┘
```

---

## Component Details

### 1. **PDF Loader** (`src/pdf_loader.py`)

**Purpose:** Extract text from PDF files

**Key Methods:**
- `load_pdf(pdf_path)` - Loads a single PDF and extracts text
- `load_multiple_pdfs(pdf_dir)` - Batch load PDFs from a directory

**Process:**
```
PDF File 
   ↓
PyPDF2 Reader
   ↓
Page-by-page text extraction
   ↓
Combined text output
```

**Example:**
```python
loader = PDFLoader()
text = loader.load_pdf("/path/to/document.pdf")
# Returns: Full text content extracted from PDF
```

---

### 2. **Text Chunker** (`src/chunker.py`)

**Purpose:** Split long text into semantically meaningful overlapping chunks

**Configuration:**
- `chunk_size`: 256 characters per chunk
- `overlap`: 50 characters overlap between consecutive chunks
- `min_chunk_size`: 100 characters minimum

**Process:**
```
Raw Text (1000+ characters)
   ↓
Clean whitespace & normalize
   ↓
Split at sentence boundaries
   ↓
Create overlapping chunks (256 chars with 50 char overlap)
   ↓
List of chunks with metadata (source, chunk_index, position)
```

**Example:**
```
Original text: "The quick brown fox jumps over the lazy dog. The dog was sleeping."

Chunk 1: "The quick brown fox jumps over the lazy dog."
Chunk 2: "brown fox jumps over the lazy dog. The dog was sleeping."
         (overlaps with Chunk 1 by 50 chars)
```

---

### 3. **Embedder** (`src/embedder.py`)

**Purpose:** Convert text into vector embeddings for semantic search

**Supported Providers:**
- **Gemini** (Google) - Default
  - Embedding: `gemini-embedding-001`
  - Generation: `gemini-2.5-flash`
  
- **Groq** - Fast inference
  - Embedding: `local-hash-embedding`
  - Generation: `llama-3.3-70b-versatile`
  
- **Perplexity** - Research-focused
  - Embedding: `pplx-embed-v1-4b`
  - Generation: `sonar-reasoning-pro`

**Key Methods:**
- `create_embedding(text)` - Single text → embedding vector
- `create_embeddings(texts)` - Batch embeddings (50 at a time)
- `generate_answer(question, context_chunks)` - Generate response using LLM

**Embedding Process:**
```
Text Chunk
   ↓
API Call (Gemini/Groq/Perplexity)
   ↓
768-dimensional vector
(numerical representation of semantic meaning)
   ↓
Stored with metadata
```

---

### 4. **Vector Database** (`src/vector_db.py`)

**Purpose:** Store and retrieve embeddings using semantic similarity search

**Database:** Pinecone (Cloud-hosted)
- Index name: `rag-documents`
- Dimension: 768
- Metric: Cosine similarity

**Key Methods:**
- `add_documents(chunks)` - Store chunks with embeddings
- `search(query_embedding, top_k)` - Find similar documents
- `get_document_count()` - Retrieve index statistics

**Storage Format:**
```
{
  "id": "document_path_chunk_0",
  "values": [0.123, -0.456, 0.789, ...],  // 768-dimensional vector
  "metadata": {
    "source": "path/to/document.pdf",
    "text": "chunk content",
    "chunk_index": 0
  }
}
```

---

### 5. **RAG Pipeline Orchestrator** (`src/rag_pipeline.py`)

**Purpose:** Coordinate all components for ingestion and querying

**Key Methods:**
- `ingest_pdf(pdf_path)` - Single PDF ingestion
- `ingest_multiple_pdfs(pdf_directory)` - Batch ingestion
- `query_and_answer(question, top_k)` - Query and generate answer
- `retrieve(question, top_k)` - Semantic search only
- `get_stats()` - Get index statistics

---

## Data Flow

### Ingestion Flow (One-Time Setup)

```
User uploads PDFs to /data/pdfs/
        ↓
    [INGESTION PHASE]
        ↓
1. PDF LOADING
   └─→ PDFLoader.load_pdf()
       • Read PDF file
       • Extract text page-by-page
       • Output: Raw text string
        ↓
2. TEXT CHUNKING
   └─→ TextChunker.chunk_text()
       • Clean and normalize text
       • Split into 256-char chunks
       • Add 50-char overlap
       • Output: List of chunk dictionaries
        ↓
3. EMBEDDING GENERATION (Batched)
   └─→ Embedder.create_embeddings()
       • Process 50 chunks per batch
       • Convert text → 768-dim vectors
       • Add semantic meaning representation
       • Output: Chunks with embedding vectors
        ↓
4. VECTOR STORAGE
   └─→ VectorDatabase.add_documents()
       • Upload to Pinecone
       • Store embeddings with metadata
       • Make searchable
        ↓
    READY FOR QUERIES
```

**Execution Time:** 
- Small PDF (10 pages): ~2-5 seconds
- Large PDF (100+ pages): ~30-60 seconds
- Batch (10 PDFs): ~5-10 minutes

---

### Query Flow (Happens Every Time User Asks a Question)

```
User enters question in React UI
        ↓
    [QUERY PHASE]
        ↓
1. QUESTION EMBEDDING
   └─→ Question → Embedder.create_embedding()
       • Convert question to 768-dim vector
       • Output: Question embedding
        ↓
2. SEMANTIC SEARCH
   └─→ VectorDatabase.search(question_embedding, top_k=3)
       • Calculate similarity with stored embeddings
       • Find most relevant chunks
       • Output: Top 3 similar document chunks
        ↓
3. CONTEXT BUILDING
   └─→ Extract text from top 3 chunks
       • Format context from retrieved documents
       • Output: Concatenated context string
        ↓
4. ANSWER GENERATION
   └─→ Embedder.generate_answer(question, context)
       • Send to LLM with question + context
       • LLM generates informed response
       • Output: Answer string
        ↓
5. RESPONSE FORMATTING
   └─→ Return to Frontend
       • Question
       • Answer
       • Source chunks (with scores)
       • Document count
        ↓
    DISPLAYED IN UI
```

**Query Time:** ~1-3 seconds (mostly network/API latency)

---

## Ingestion Pipeline

### Step-by-Step Process

**Command:** 
```bash
python ingest_optimized.py
```

**Detailed Breakdown:**

1. **Initialization**
   ```
   Load config from settings.py
   Initialize RAGPipeline with config
   Connect to Pinecone
   Authenticate with Gemini/Groq/Perplexity
   ```

2. **PDF Loading**
   ```
   Find all .pdf files in /data/pdfs/
   For each PDF:
     • Open with PyPDF2
     • Extract text from each page
     • Combine into single string
     • Log progress
   ```

3. **Text Chunking**
   ```
   Clean text (normalize whitespace)
   While text remaining:
     • Take 256 characters
     • Try to break at sentence boundary
     • Create chunk with metadata
     • Set overlap to next chunk (50 chars)
     • Move to next chunk
   ```

4. **Embedding Generation (Batched)**
   ```
   Group chunks into batches of 50
   For each batch:
     • Extract text from chunks
     • Call embedding API
     • Receive 768-dimensional vectors
     • Attach vectors to chunks
     • Log batch progress
   ```

5. **Pinecone Storage**
   ```
   Format vectors for Pinecone:
     • id: unique identifier
     • values: 768-dim embedding
     • metadata: source, text, chunk_index
   Upload to Pinecone index
   Log success/failure
   ```

**Example Output:**
```
Starting ingestion...
Processing PDF: research_paper.pdf
  - Extracted 5000 characters
  - Created 20 chunks
  - Generated 20 embeddings in 1 batch
  - Stored 20 chunks in Pinecone
  
Ingestion complete!
Total documents in index: 145
```

---

## Query Pipeline

### Step-by-Step Process

**Endpoint:** `POST /api/query`

**Request:**
```json
{
  "question": "What is machine learning?",
  "top_k": 3
}
```

**Detailed Breakdown:**

1. **Question Embedding**
   ```
   Input: "What is machine learning?"
   
   Embedder.create_embedding(question)
   └─ Task type: "RETRIEVAL_QUERY"
   └─ Output: [0.123, -0.456, 0.789, ..., 0.234]
              (768 dimensions)
   ```

2. **Semantic Search**
   ```
   VectorDatabase.search(question_embedding, top_k=3)
   
   Pinecone calculates cosine similarity:
   similarity = dot(question_vec, doc_vec) / (norm(question_vec) * norm(doc_vec))
   
   Returns: Top 3 chunks sorted by similarity score
   ```

3. **Retrieved Context**
   ```
   Chunk 1 (score: 0.89):
     "Machine learning is a subset of artificial intelligence..."
   
   Chunk 2 (score: 0.87):
     "ML algorithms learn from data without explicit programming..."
   
   Chunk 3 (score: 0.84):
     "Supervised learning, unsupervised learning, and..."
   ```

4. **Answer Generation**
   ```
   Prompt to LLM:
   ─────────────
   Context:
   [Insert retrieved chunks]
   
   Question: What is machine learning?
   
   [LLM generates answer based on context]
   
   Response: "Machine learning is a branch of AI where..."
   ```

5. **Response Formatting**
   ```json
   {
     "question": "What is machine learning?",
     "answer": "Machine learning is a branch of AI...",
     "source_chunks": [
       {
         "source": "AI_Basics.pdf",
         "score": 0.89,
         "text": "Machine learning is a subset of..."
       }
     ],
     "total_documents": 145
   }
   ```

---

## API Endpoints

### 1. Health Check
**Endpoint:** `GET /api/health`

**Purpose:** Verify backend is running and check system status

**Response:**
```json
{
  "status": "healthy",
  "total_documents": 145,
  "models": {
    "provider": "GROQ",
    "embedding_model": "local-hash-embedding",
    "generation_model": "llama-3.3-70b-versatile"
  }
}
```

---

### 2. Query
**Endpoint:** `POST /api/query`

**Purpose:** Submit question and get AI-generated answer

**Request:**
```json
{
  "question": "Explain neural networks",
  "top_k": 3
}
```

**Response:**
```json
{
  "question": "Explain neural networks",
  "answer": "Neural networks are computing systems inspired by biological neural networks...",
  "source_chunks": [
    {
      "source": "deep_learning_guide.pdf",
      "score": 0.92,
      "text": "A neural network consists of interconnected nodes..."
    },
    {
      "source": "ai_fundamentals.pdf",
      "score": 0.87,
      "text": "Nodes are connected with weights that adjust during training..."
    }
  ],
  "total_documents": 145
}
```

**Error Response (No documents):**
```json
{
  "error": "No documents found in the index. Please ingest PDFs first."
}
```

---

### 3. Models Information
**Endpoint:** `GET /api/models`

**Purpose:** Get current AI models configuration

**Response:**
```json
{
  "provider": "GROQ",
  "embedding_model": "local-hash-embedding",
  "generation_model": "llama-3.3-70b-versatile"
}
```

---

## Configuration

### Configuration File: `config/settings.py`

```python
# LLM Provider (gemini, groq, or perplexity)
LLM_PROVIDER = "groq"

# Chunking Configuration
CHUNK_SIZE = 256              # Characters per chunk
CHUNK_OVERLAP = 50            # Overlap between chunks
MIN_CHUNK_SIZE = 100          # Minimum chunk size

# Embedding Configuration
EMBEDDING_DIMENSION = 768     # Vector dimension
EMBEDDING_BATCH_SIZE = 50     # Chunks per batch

# Vector Database
VECTOR_DB_NAME = "rag-documents"  # Pinecone index name

# RAG Parameters
TOP_K_RESULTS = 5             # Default results per query
SIMILARITY_THRESHOLD = 0.6    # Minimum similarity score

# API Keys (from environment or defaults)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
```

### Environment Variables (.env)

```env
# LLM Configuration
LLM_PROVIDER=groq
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here

# Vector Database
PINECONE_API_KEY=your_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-documents

# Chunk Settings
CHUNK_SIZE=256
CHUNK_OVERLAP=50
EMBEDDING_BATCH_SIZE=50
```

---

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 14+ (for React frontend)
- API keys from:
  - Pinecone (https://pinecone.io)
  - Gemini/Groq/Perplexity (choose one or more)

### 1. Backend Setup

```bash
# Navigate to project
cd RAG-pipeline

# Create virtual environment
python -m venv ainv
source ainv/bin/activate  # On Windows: ainv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file with your API keys
touch .env
# Edit .env with your configuration

# Create data directories
mkdir -p data/pdfs data/vector_store

# Place your PDF files in data/pdfs/
cp /path/to/your/pdfs/* data/pdfs/
```

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Environment configuration (if needed)
# Create .env file with API URL
echo "REACT_APP_API_URL=http://localhost:5001" > .env
```

### 3. Ingest PDFs

```bash
# From RAG-pipeline directory
python ingest_optimized.py

# Or use the batch script
python trigger_pipeline.py
```

### 4. Start Services

**Terminal 1 - Flask Backend:**
```bash
cd RAG-pipeline
source ainv/bin/activate
python -m flask run --port 5001
```

**Terminal 2 - React Frontend:**
```bash
cd RAG-pipeline/frontend
npm start
# Opens http://localhost:3000
```

**Access the Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001/api

---

## Usage Examples

### Example 1: Ingest a Single PDF

```python
from config.settings import CONFIG
from src.rag_pipeline import RAGPipeline

# Initialize pipeline
pipeline = RAGPipeline(config=CONFIG)

# Ingest a PDF
result = pipeline.ingest_pdf("data/pdfs/my_document.pdf")
print(result)
# Output: {'status': 'success', 'pdf_path': '...', 'total_chunks': 45, 'stored_chunks': 45}
```

### Example 2: Query the Pipeline

```python
from config.settings import CONFIG
from src.rag_pipeline import RAGPipeline

# Initialize pipeline
pipeline = RAGPipeline(config=CONFIG)

# Ask a question
result = pipeline.query_and_answer("What is the main topic?", top_k=3)

print("Question:", result['question'])
print("Answer:", result['answer'])
print("Sources:")
for chunk in result['source_chunks']:
    print(f"  - {chunk['source']}: {chunk['text'][:100]}...")
```

### Example 3: Using the API

```bash
# Health check
curl http://localhost:5001/api/health

# Query
curl -X POST http://localhost:5001/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main finding?",
    "top_k": 3
  }'

# Get models info
curl http://localhost:5001/api/models
```

### Example 4: React Component Query

```javascript
// In RAGInterface.js
const handleSubmit = async (e) => {
  e.preventDefault();
  
  try {
    const response = await axios.post('http://localhost:5001/api/query', {
      question: userQuestion,
      top_k: 3
    });
    
    setAnswer(response.data.answer);
    setSources(response.data.source_chunks);
  } catch (err) {
    setError(err.response?.data?.error);
  }
};
```

---

## Performance Considerations

### Latency Breakdown (Query)

```
Question Embedding:     ~200ms (API call)
Semantic Search:        ~50ms  (Pinecone)
Context Formatting:     ~10ms  (Local)
Answer Generation:      ~1500ms (LLM API)
Response Formatting:    ~5ms  (Local)
─────────────────────────────
Total:                  ~1.8 seconds
```

### Optimization Tips

1. **Chunking**
   - Smaller chunks (256 chars) = more specific retrieval
   - Larger chunks (1000+ chars) = more context
   - Overlap = better continuity but more storage

2. **Batch Processing**
   - Embedding 50 chunks at once is faster than 1-by-1
   - Reduces API calls and overhead

3. **Top-K Results**
   - k=3: Faster, less context
   - k=5+: More comprehensive but slower

4. **Provider Choice**
   - Groq: Fastest (inference focused)
   - Gemini: Balanced
   - Perplexity: Best for reasoning

---

## Troubleshooting

### Issue: "Failed to connect to backend"
- Ensure Flask is running on port 5001
- Check if firewall allows localhost:5001
- Verify CORS is enabled in Flask

### Issue: "No documents found in the index"
- Run `python ingest_optimized.py` first
- Check if PDFs are in `data/pdfs/`
- Verify Pinecone credentials in .env

### Issue: "Slow query responses"
- Check internet connection
- Reduce `top_k` parameter
- Try a different LLM provider

### Issue: API key errors
- Verify .env file has all required keys
- Check key validity in provider dashboard
- Ensure correct environment variable names

---

## Architecture Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | React + Axios | User interface |
| Backend | Flask + CORS | REST API |
| PDF Processing | PyPDF2 | Text extraction |
| Text Processing | Custom Chunker | Semantic chunks |
| Embeddings | Gemini/Groq/Perplexity | Vector representations |
| Vector DB | Pinecone | Semantic search |
| Orchestration | Python | Pipeline coordination |

---

## Key Metrics

- **Embedding Dimension:** 768
- **Chunk Size:** 256 characters
- **Chunk Overlap:** 50 characters
- **Batch Size:** 50 chunks
- **Top-K Results:** 3-5 documents
- **Storage:** Pinecone Cloud
- **Query Latency:** ~1.8 seconds
- **Ingestion Speed:** ~5-10 sec/PDF

---

## Next Steps

1. ✅ Set up environment and dependencies
2. ✅ Configure API keys in .env
3. ✅ Add PDFs to `data/pdfs/`
4. ✅ Run ingestion pipeline
5. ✅ Start backend and frontend
6. ✅ Test via web UI
7. ✅ Monitor performance and adjust config as needed

---

## Support & Resources

- Pinecone Docs: https://docs.pinecone.io
- Google Gemini: https://ai.google.dev
- Groq: https://console.groq.com
- Perplexity: https://docs.perplexity.ai
- Flask: https://flask.palletsprojects.com
- React: https://react.dev

