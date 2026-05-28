# Transaction Extraction from Bank Statements

## Overview
The RAG pipeline now includes advanced transaction extraction capabilities that parse bank statement PDFs and extract individual transaction details (merchant name, amount, category, date) for spending analysis.

## New Components

### 1. **TransactionExtractor** (`src/transaction_extractor.py`)
Main class for extracting and chunking transaction data from bank statements.

#### Key Methods:

- **`extract_transactions(text, source)`**
  - Parses transaction lines from bank statement text
  - Returns list of transaction dictionaries with:
    - `date`: Transaction date (DD-MMM-YYYY)
    - `description`: Merchant/payee name
    - `category`: Transaction category (Grocery, Restaurants, Services, etc.)
    - `amount`: Amount in rupees
    - `amount_formatted`: Formatted with currency symbol
    - `is_credit`: Boolean indicating if credit transaction

- **`create_transaction_chunks(transactions, chunk_size)`**
  - Groups multiple transactions together (default 5 per chunk)
  - Creates chunks that preserve transaction structure
  - Returns list of chunk dictionaries with:
    - `content`: Formatted transaction text
    - `transactions`: List of transaction dicts
    - `transaction_count`: Number of transactions
    - `total_amount`: Sum of amounts
    - `categories`: Unique categories in chunk
    - `date_range`: Date span of transactions

- **`create_spending_summary_chunks(transactions)`**
  - Groups transactions by category
  - Creates category-wise spending summaries
  - Returns list of summary chunks with:
    - `category`: Spending category
    - `total_amount`: Total spent in category
    - `transaction_count`: Number of transactions
    - Details list of all transactions in category

### 2. **RAGPipeline Extensions** (`src/rag_pipeline.py`)
New methods added to the RAGPipeline class:

- **`ingest_pdf_with_transactions(pdf_path, extraction_type)`**
  - Ingests a single PDF with transaction extraction
  - Parameters:
    - `pdf_path`: Path to the PDF file
    - `extraction_type`: "grouped" (default) or "summary"
  - Returns metadata about ingestion

- **`ingest_all_pdfs_with_transactions(pdf_directory, extraction_type)`**
  - Batch ingests all PDFs in a directory
  - Extracts transactions from each PDF
  - Creates embeddings and stores in vector database
  - Returns aggregated statistics

## Usage Examples

### Example 1: Extract and Display Transactions
```python
from src.pdf_loader import PDFLoader
from src.transaction_extractor import TransactionExtractor

# Load and extract
loader = PDFLoader()
extractor = TransactionExtractor()

text = loader.load_pdf("data/pdfs/kotak.pdf")
transactions = extractor.extract_transactions(text, source="kotak.pdf")

# Display results
for txn in transactions:
    print(f"{txn['date']} - {txn['description']} ({txn['category']}) - {txn['amount_formatted']}")
```

### Example 2: Create Transaction Chunks for RAG
```python
# Create grouped transaction chunks (5 transactions per chunk)
grouped_chunks = extractor.create_transaction_chunks(transactions, chunk_size=5)

# Create spending summary by category
summary_chunks = extractor.create_spending_summary_chunks(transactions)

for chunk in summary_chunks:
    print(f"\n{chunk['category']}: {chunk['total_amount']:.2f}")
    print(chunk['content'])
```

### Example 3: Ingest with RAGPipeline
```python
from src.rag_pipeline import RAGPipeline
from config.settings import CONFIG

pipeline = RAGPipeline(CONFIG)

# Ingest all PDFs with transaction extraction
result = pipeline.ingest_all_pdfs_with_transactions(
    pdf_directory="data/pdfs",
    extraction_type="grouped"  # or "summary"
)

print(f"Extracted {result['total_transactions']} transactions")
print(f"Created {result['total_chunks']} chunks")
print(f"Stored {result['total_stored']} chunks in vector DB")
```

### Example 4: Run Demo Script
```bash
cd RAG-pipeline
python3 extract_transactions_demo.py
```

This will:
1. Load all PDFs from `data/pdfs/`
2. Extract transaction details
3. Display spending statistics
4. Create sample transaction chunks
5. Show spending summaries by category

## Output Example

```
Transaction Details:
- 16-Apr-2026 - UPI-952265836823-ANAMALA MALLE (Grocery) - ₹60.00
- 18-Apr-2026 - UPI-461840784686-MRS ANUSUYA W (Restaurants) - ₹50.00
- 21-Apr-2026 - UPI-213262667191-RADHAKRISHNAM (Grocery) - ₹50.00

Spending Summary:
- Grocery: ₹1,331.00 (15 transactions)
- Restaurants: ₹895.00 (8 transactions)
- Services: ₹590.00 (3 transactions)
```

## Features

✅ Extracts merchant names and spending amounts
✅ Categorizes transactions automatically
✅ Groups transactions for context-aware chunking
✅ Creates spending summaries by category
✅ Generates embeddings for RAG retrieval
✅ Stores in vector database for semantic search
✅ Handles both debit and credit transactions

## Benefits

1. **Better Spending Insights**: Ask questions like "How much did I spend on groceries?" or "What are my top spending categories?"
2. **Organized Chunking**: Each chunk contains complete transaction information, not random text fragments
3. **Category-Based Search**: Retrieve all transactions from a specific spending category
4. **Transaction Timeline**: Understand spending patterns over time

## Sample Queries (After Ingestion)

- "How much did I spend on food and restaurants in May?"
- "What was my total spending on services?"
- "Show me all transactions from Swiggy"
- "What are my top 5 spending categories?"
- "Compare my grocery spending across different dates"
