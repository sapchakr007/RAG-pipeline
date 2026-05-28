# Transaction Ingestion and Query Guide

## Quick Start

### Step 1: Configure which PDFs to exclude (Optional)
Edit `pdf_config.py` and uncomment to exclude specific PDFs:
```python
EXCLUDED_PDFS = [
    "kotak.pdf"  # Uncomment to exclude static PDFs
]
```

### Step 2: Ingest New PDFs
```bash
python3 ingest_transactions.py
```

**What it does:**
- Detects new PDFs in `data/pdfs/`
- Skips already-processed PDFs (tracked in `data/processed_pdfs.json`)
- Skips excluded PDFs (from `pdf_config.py`)
- Extracts transactions from each new PDF
- Creates transaction chunks
- Generates embeddings
- Stores in Pinecone vector database

**Output:**
```
📥 PDF Transaction Ingestion - Processing New PDFs Only

📊 PDF Status:
  Total PDFs in data/pdfs/: 2
  Already processed: 1
  Excluded from processing: 1
    - kotak.pdf
  New PDFs to ingest: 0

✅ No new PDFs to process.
```

---

### Step 3: Query Your Spending
```bash
python3 query_transactions.py
```

**Interactive Query Mode:**
```
❓ Your question: How much did I spend on groceries?

💡 Answer:
Based on the transactions, you spent ₹1,331.00 on groceries...

📚 Source Transactions:
1. 16-Apr-2026 - ANAMALA MALLE (Grocery) - ₹60.00
2. 21-Apr-2026 - RADHAKRISHNAM (Grocery) - ₹50.00
...
```

---

## Adding New PDFs

1. **Add PDF to folder:**
   ```bash
   cp your_statement.pdf data/pdfs/
   ```

2. **Run ingestion (automatically processes new PDFs only):**
   ```bash
   python3 ingest_transactions.py
   ```

3. **Query immediately:**
   ```bash
   python3 query_transactions.py
   ```

---

## How It Works

### Ingestion Flow
```
New PDF → Extract Transactions → Create Chunks → Generate Embeddings → Store in Vector DB
```

### Query Flow
```
Question → Create Embedding → Search Vector DB → Retrieve Relevant Chunks → LLM generates Answer
```

---

## Configuration Options

**File:** `pdf_config.py`

```python
# Exclude specific PDFs from processing
EXCLUDED_PDFS = ["kotak.pdf", "old_statements.pdf"]

# Extraction type: "grouped" (groups transactions) or "summary" (by category)
DEFAULT_EXTRACTION_TYPE = "grouped"

# Transactions per chunk
CHUNK_SIZE = 5

# Results to retrieve for queries
TOP_K_RESULTS = 5
```

---

## Processing Status

**File:** `data/processed_pdfs.json`

Automatically tracks which PDFs have been processed:
```json
{
  "processed": ["kotak.pdf", "statement2.pdf"],
  "last_updated": "2026-05-23T10:30:00"
}
```

---

## Example Queries

Once you've ingested transactions, try these questions:

- "How much did I spend on groceries?"
- "What are my top spending categories?"
- "Show all restaurant transactions"
- "How much did I spend on services?"
- "Compare my spending by category"
- "Which merchant did I spend the most on?"
- "What was my total spending this month?"

---

## Troubleshooting

### No new PDFs found
- Check that PDF is in `data/pdfs/` folder
- PDFs are not excluded in `pdf_config.py`
- PDF hasn't been processed before (check `data/processed_pdfs.json`)

### Query returns no results
- Make sure you've run `ingest_transactions.py` first
- Check that your question is related to spending/transactions
- Try a more specific question

### Embedding errors
- Ensure Google Generative AI is configured
- Check API keys in `config/settings.py`

---

## File Structure

```
RAG-pipeline/
├── ingest_transactions.py      # ← Run this to ingest PDFs
├── query_transactions.py        # ← Run this to ask questions
├── pdf_config.py               # ← Configure excluded PDFs
├── data/
│   ├── pdfs/                   # ← Add your PDFs here
│   │   ├── kotak.pdf           # (existing/excluded)
│   │   └── new_statement.pdf   # (will be ingested)
│   └── processed_pdfs.json     # Auto-generated tracking
└── src/
    └── transaction_extractor.py
```
