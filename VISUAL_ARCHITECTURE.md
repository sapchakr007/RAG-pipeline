# RAG Pipeline - Visual Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE SYSTEM                          │
└─────────────────────────────────────────────────────────────────┘

                          INPUT
                            │
                    ┌───────▼────────┐
                    │   PDF Files    │
                    │  (User adds)   │
                    └───────┬────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
    ┌─────────┐                          ┌──────────┐
    │ Single  │                          │ Multiple │
    │ PDF     │                          │ PDFs     │
    └────┬────┘                          └────┬─────┘
         │                                    │
         │ ingest_pdf()                       │ ingest_multiple_pdfs()
         │                                    │
         └────────────────┬───────────────────┘
                          │
                          ▼
                 ┌────────────────────┐
                 │  PDF LOADER        │
                 │  (pdf_loader.py)   │
                 │                    │
                 │  Extract Text      │
                 │  From PDFs         │
                 └────────┬───────────┘
                          │
                       RAW TEXT
                          │
                          ▼
                 ┌────────────────────┐
                 │ TEXT CHUNKER       │
                 │ (chunker.py)       │
                 │                    │
                 │ Split into         │
                 │ Overlapping        │
                 │ Chunks             │
                 └────────┬───────────┘
                          │
                    TEXT CHUNKS
                  (with metadata)
                          │
                          ▼
                 ┌────────────────────┐
                 │ EMBEDDER           │
                 │ (embedder.py)      │
                 │                    │
                 │ Create 768-dim     │
                 │ Vectors via        │
                 │ Gemini API         │
                 └────────┬───────────┘
                          │
              CHUNKS + EMBEDDINGS
                          │
                          ▼
                 ┌────────────────────┐
                 │ VECTOR DATABASE    │
                 │ (vector_db.py)     │
                 │ ChromaDB           │
                 │                    │
                 │ Persistent         │
                 │ Storage            │
                 └────────┬───────────┘
                          │
                  ┌───────┴──────────────┐
                  │                      │
        ┌─────────▼────────┐    ┌────────▼──────────┐
        │   QUERY INPUT    │    │  Vector Store     │
        │   (User enters)  │    │  (data/vector_*)  │
        └─────────┬────────┘    └──────────────────┘
                  │
         retrieve(query, top_k)
                  │
                  ▼
        ┌──────────────────┐
        │ Embed Query      │
        │ (768-dim)        │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Semantic Search  │
        │ (Cosine Sim)     │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │  Top-K Results   │
        │  (ranked by      │
        │   relevance)     │
        └────────┬─────────┘
                 │
                 ▼
        [Return to User]
```

## Data Flow - Ingestion Pipeline

```
PDF FILE
   │
   ├─ load_pdf()
   │  └─► RAW TEXT
   │
   ├─ chunk_text()
   │  └─► CHUNKS
   │      ├─ id: "source_chunk_0"
   │      ├─ content: "text..."
   │      ├─ source: "document.pdf"
   │      └─ chunk_index: 0
   │
   ├─ create_embedding()
   │  └─► EMBEDDING (768 dimensions)
   │      [0.12, -0.34, 0.56, ..., 0.89]
   │
   └─ add_documents()
      └─► STORED IN ChromaDB
          ├─ Collection: "rag_documents"
          ├─ Indexed for fast search
          └─ Persistent storage
```

## Data Flow - Retrieval Pipeline

```
QUERY
  │
  ├─ User: "What is machine learning?"
  │
  ├─ create_embedding()
  │  └─► QUERY EMBEDDING (768 dimensions)
  │
  ├─ search()
  │  └─► SEMANTIC SEARCH
  │      ├─ Method: Cosine Similarity
  │      ├─ Top-K: 5
  │      └─ Threshold: 0.6
  │
  └─► RESULTS
      ├─ Result 1: {
      │    id: "document_chunk_3",
      │    content: "Machine learning is...",
      │    source: "document.pdf",
      │    distance: 0.15 ◄── Low = More Similar
      │  }
      ├─ Result 2: { ... }
      ├─ Result 3: { ... }
      ├─ Result 4: { ... }
      └─ Result 5: { ... }
```

## Component Interaction Diagram

```
                    ┌─────────────────┐
                    │  RAGPipeline    │
                    │  (Main Class)   │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
      ┌──────────┐    ┌──────────┐    ┌──────────┐
      │PDFLoader │    │TextChunker  │TextChunker│
      │          │    │          │    │          │
      │load_pdf()    │chunk_text()   │embed_    │
      └──────────┘    └──────────┘    │chunks()  │
                                      └──────────┘
                                           │
                                    ┌──────▼────────┐
                                    │GeminiEmbedder │
                                    │               │
                                    │create_        │
                                    │embedding()    │
                                    └──────┬────────┘
                                           │
                                    ┌──────▼────────┐
                                    │ VectorDatabase│
                                    │               │
                                    │ ChromaDB      │
                                    │               │
                                    │search()       │
                                    │add_documents()
                                    └───────────────┘
                                           │
                                    Persistent Storage
                                    data/vector_store/
```

## Processing Pipeline Stages

```
STAGE 1: PDF EXTRACTION
───────────────────────
PDF File
   │
   ├─ Open & Read
   ├─ Extract Text per Page
   ├─ Combine Text
   └─► RAW DOCUMENT TEXT


STAGE 2: TEXT PROCESSING
────────────────────────
Raw Text
   │
   ├─ Clean & Normalize
   ├─ Remove Extra Spaces/Newlines
   └─► CLEANED TEXT


STAGE 3: CHUNKING
─────────────────
Cleaned Text
   │
   ├─ Split into Size Chunks (1000 chars)
   ├─ Add Overlap (200 chars)
   ├─ Find Sentence Boundaries
   └─► CHUNKS
       (Each chunk ~1KB)


STAGE 4: EMBEDDING
──────────────────
Chunks
   │
   ├─ For Each Chunk:
   │  ├─ Send to Gemini API
   │  ├─ Create 768-dim Vector
   │  └─ Rate Limit (2s delay/batch)
   └─► CHUNKS + EMBEDDINGS


STAGE 5: STORAGE
────────────────
Chunks + Embeddings
   │
   ├─ Create Records
   ├─ Add Metadata
   ├─ Index Vectors
   └─► ChromaDB
       (Persistent)


STAGE 6: RETRIEVAL
──────────────────
Query
   │
   ├─ Embed Query (same way as chunks)
   ├─ Search Vector DB
   ├─ Rank by Similarity
   └─► TOP-K RESULTS
       (Ranked by relevance)
```

## Class Hierarchy

```
RAGPipeline (Main Class)
│
├─► PDFLoader
│   └─ load_pdf()
│   └─ load_multiple_pdfs()
│
├─► TextChunker
│   └─ chunk_text()
│   └─ chunk_multiple_texts()
│   └─ _clean_text()
│
├─► GeminiEmbedder
│   └─ create_embedding()
│   └─ create_embeddings_batch()
│   └─ embed_chunks()
│
└─► VectorDatabase
    └─ add_documents()
    └─ search()
    └─ get_document_count()
    └─ get_all_documents()
    └─ delete_all()
```

## Configuration Hierarchy

```
┌─ Config Dictionary (Highest Priority)
│  └─ Passed to RAGPipeline()
│
├─ .env File (Medium Priority)
│  └─ Loaded by python-dotenv
│
└─ Default Settings (Lowest Priority)
   └─ config/settings.py
```

## Storage Architecture

```
PROJECT ROOT
│
├── data/
│   │
│   ├── pdfs/
│   │   ├── document1.pdf  ◄─── USER ADDS PDF FILES
│   │   ├── document2.pdf
│   │   └── ...
│   │
│   └── vector_store/
│       ├── .chroma/       ◄─── CHROMADB STORAGE (Auto-created)
│       ├── chroma.sqlite3 (Vector Index)
│       └── Metadata Files
│
└── config/
    └── settings.py        ◄─── CONFIGURATION
```

## Embedding Vector Representation

```
Each Chunk → 768-Dimensional Vector

┌─────────────────────────────────────────┐
│ "Machine learning uses patterns..."      │
│            (Input Text)                  │
└──────────────────┬──────────────────────┘
                   │
            (Gemini API)
                   │
┌──────────────────▼──────────────────────┐
│  [0.125, -0.342, 0.568, ..., 0.891]    │
│         768 Dimensions                  │
│    (Semantic Representation)             │
└──────────────────┬──────────────────────┘
                   │
            (Store in DB)
                   │
        Used for Similarity Search
        (Cosine Similarity)
```

## Search Process

```
QUERY: "What is ML?"
       │
       ▼
    Embed Query
    (768-dim)
       │
       ▼
    Compare with Stored Vectors
    (Cosine Similarity)
       │
       ├─► Chunk A: 0.92 similarity
       ├─► Chunk B: 0.88 similarity
       ├─► Chunk C: 0.75 similarity
       ├─► Chunk D: 0.65 similarity
       └─► Chunk E: 0.61 similarity
       │
       ▼
    Sort by Score (Descending)
       │
       ▼
    Return Top-K (e.g., top 5)
       │
       ▼
    Display Results
    (Most relevant first)
```

## File Organization

```
Source Code Modules (src/)
├── pdf_loader.py        ◄─ PDF Text Extraction
├── chunker.py           ◄─ Text Splitting
├── embedder.py          ◄─ Vector Creation
├── vector_db.py         ◄─ Database Operations
└── rag_pipeline.py      ◄─ Main Orchestration


Configuration (config/)
├── settings.py          ◄─ All Settings
└── __init__.py          ◄─ Package Init


Data (data/)
├── pdfs/                ◄─ Input PDFs
└── vector_store/        ◄─ Embedded Vectors


Documentation (root)
├── README.md            ◄─ Main Guide
├── QUICKSTART.md        ◄─ Quick Start
├── CONFIG_GUIDE.md      ◄─ Configuration Details
├── ARCHITECTURE.md      ◄─ Design Details
└── API_REFERENCE.md     ◄─ API Documentation


Executables (root)
├── main.py              ◄─ Simple Entry Point
└── example_usage.py     ◄─ Usage Examples


Testing (tests/)
└── test_pipeline.py     ◄─ Unit Tests
```

## Pipeline Performance Overview

```
INGESTION PERFORMANCE
─────────────────────
Input:  Large PDF (10MB, 50 pages)
        ↓
Time:   ~5-30 seconds (depends on API calls)
        ├─ PDF Loading:    <1 second
        ├─ Chunking:       <1 second
        ├─ Embeddings:     3-20 seconds (API dependent)
        └─ Storage:        <1 second
Output: ~200 chunks with embeddings


RETRIEVAL PERFORMANCE
─────────────────────
Input:  Query ("What is...")
        ↓
Time:   ~1-3 seconds
        ├─ Query Embedding:  1-2 seconds (API)
        └─ Vector Search:    ~100ms (local)
Output: Top-5 relevant chunks


MEMORY USAGE
────────────
Per 100 chunks:
├─ Vectors: ~300KB (100 × 3KB per 768-dim vector)
├─ Text:    ~500KB (average text storage)
├─ Metadata: ~50KB
└─ Total:   ~850KB - 1MB

Per 10,000 chunks: ~100MB
Per 100,000 chunks: ~1GB
```

---

This visual architecture helps understand how all components work together to process documents and enable semantic search.
