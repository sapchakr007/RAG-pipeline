# RAG Pipeline - CLI Tools

## Overview

Two standalone command-line scripts for managing the RAG Pipeline:
- **`cli_ingest.py`** - Ingest PDFs into the vector database
- **`cli_query.py`** - Query ingested documents

---

## CLI Ingest Tool

### Usage

```bash
python cli_ingest.py [OPTIONS]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--file PATH` | `-f` | Ingest a specific PDF file |
| `--dir PATH` | `-d` | Ingest from custom directory (default: `data/pdfs/`) |
| `--skip-confirm` | | Skip confirmation prompts |
| `--verbose` | `-v` | Enable verbose logging |
| `--help` | `-h` | Show help message |

### Examples

**Ingest all PDFs from default directory:**
```bash
python cli_ingest.py
```

**Ingest a specific file:**
```bash
python cli_ingest.py --file data/pdfs/report.pdf
python cli_ingest.py -f /path/to/document.pdf
```

**Ingest from custom directory:**
```bash
python cli_ingest.py --dir /path/to/pdfs
python cli_ingest.py -d ~/Documents/statements
```

**Verbose output:**
```bash
python cli_ingest.py --verbose
python cli_ingest.py -v
```

**Skip confirmation:**
```bash
python cli_ingest.py --skip-confirm
```

### Output Example

```
======================================================================
📥 RAG Pipeline - PDF Ingestion Tool
======================================================================

📄 Ingesting: report.pdf
   Size: 2.45 MB

Continue? (y/n): y

----------------------------------------------------------------------
✅ Ingestion Complete!
----------------------------------------------------------------------
Status: success
Total chunks: 45
Stored chunks: 45

----------------------------------------------------------------------
📊 Pipeline Statistics:
----------------------------------------------------------------------
Total documents in index: 312
Total chunks: 5,420

🤖 LLM Provider: GROQ
📝 Embedding Model: local-hash-embedding
💭 Generation Model: llama-3.3-70b-versatile

======================================================================
✨ Ingestion successful! Ready for queries.
======================================================================
```

---

## CLI Query Tool

### Usage

```bash
python cli_query.py [QUESTION] [OPTIONS]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `QUESTION` | | Question to ask (quoted if multiple words) |
| `--top-k N` | `-k` | Number of source chunks to retrieve (default: 3) |
| `--interactive` | `-i` | Interactive mode - ask multiple questions |
| `--verbose` | `-v` | Enable verbose logging |
| `--help` | `-h` | Show help message |

### Examples

**Single query:**
```bash
python cli_query.py "What is the main topic?"
python cli_query.py "How much was spent on groceries?" --top-k 5
```

**Interactive mode:**
```bash
python cli_query.py --interactive
python cli_query.py -i
```

**Verbose output:**
```bash
python cli_query.py "Your question?" --verbose
python cli_query.py "Question?" -v
```

### Output Example

```
======================================================================
🔍 RAG Pipeline - Document Query Tool
======================================================================

📚 Documents in index: 312
📦 Total chunks: 5,420

🤖 LLM Provider: GROQ
📝 Embedding Model: local-hash-embedding
💭 Generation Model: llama-3.3-70b-versatile

======================================================================

======================================================================
📖 Answer
======================================================================

❓ Question: What is the main topic?

💬 Answer:
The document discusses retrieval-augmented generation (RAG) systems...
[Full answer text]

----------------------------------------------------------------------
📌 Source Chunks:
----------------------------------------------------------------------

1. research_paper.pdf
   Similarity Score: 0.89
   Text: Retrieval-augmented generation combines document retrieval...

2. ai_guide.pdf
   Similarity Score: 0.85
   Text: RAG systems improve accuracy by incorporating external...

3. technical_docs.pdf
   Similarity Score: 0.78
   Text: The pipeline processes queries through multiple stages...

======================================================================
```

### Interactive Mode

In interactive mode, you can ask multiple questions in sequence:

```
💡 Tip: Type 'exit' to quit, 'clear' to clear screen

Your question: What is the first document about?

[Answer and sources displayed]

Your question: Can you summarize the key points?

[Answer and sources displayed]

Your question: exit

📊 Total queries: 2
👋 Goodbye!
```

---

## Typical Workflow

### Step 1: Ingest Documents

```bash
# Add PDFs to data/pdfs/ directory
cp /path/to/documents/* data/pdfs/

# Ingest all PDFs
python cli_ingest.py

# Or specific file
python cli_ingest.py -f data/pdfs/report.pdf
```

### Step 2: Query Documents

```bash
# Single query
python cli_query.py "What are the main findings?"

# Interactive mode
python cli_query.py -i

# Custom number of results
python cli_query.py "Topic?" --top-k 5
```

### Step 3: Analyze Results

- Answers are based on retrieved document chunks
- Similarity scores show relevance (0-1, higher is better)
- Source files are listed for traceability

---

## Advanced Usage

### Batch Ingestion with Script

```bash
#!/bin/bash
# ingest_all.sh - Ingest multiple directories

echo "Ingesting PDFs..."
python cli_ingest.py --dir data/pdfs/
python cli_ingest.py --dir data/archives/
python cli_ingest.py --dir data/reports/

echo "✅ All ingestions complete"
```

### Query with Output Redirection

```bash
# Save query results to file
python cli_query.py "Your question?" > results.txt

# Append multiple queries
python cli_query.py "Question 1?" >> results.txt
python cli_query.py "Question 2?" >> results.txt
```

### Piping Queries

```bash
# Run multiple queries from file
cat queries.txt | while read q; do
  python cli_query.py "$q"
done
```

---

## Tips & Tricks

### 1. Verbose Output
Use `-v` flag to see detailed logging:
```bash
python cli_ingest.py -v
python cli_query.py "question?" -v
```

### 2. Skip Confirmations
For automation, use `--skip-confirm`:
```bash
python cli_ingest.py --skip-confirm
```

### 3. Adjust Result Count
Get more sources for comprehensive answers:
```bash
python cli_query.py "question?" --top-k 10
```

### 4. Interactive Exploration
Use interactive mode to explore documents:
```bash
python cli_query.py -i
```

---

## Error Handling

### "No documents in index"
```bash
# Solution: Ingest PDFs first
python cli_ingest.py
```

### "File not found"
```bash
# Solution: Provide correct path
python cli_ingest.py --file /correct/path/file.pdf
```

### "No PDF files found"
```bash
# Solution: Add PDFs to directory
cp *.pdf data/pdfs/
python cli_ingest.py
```

### Connection errors
```bash
# Ensure RAG pipeline is properly initialized
python cli_query.py --verbose
```

---

## Performance Notes

- **Ingestion**: ~2-5 seconds per PDF (depends on size)
- **Query**: ~1-3 seconds (network latency + LLM inference)
- **Batch Ingestion**: Consider --skip-confirm for faster processing
- **Large Documents**: May take longer to process and embed

---

## Integration with Other Tools

### Cron Job (Daily Ingestion)

```bash
# crontab -e
0 2 * * * cd /path/to/RAG-pipeline && python cli_ingest.py --skip-confirm
```

### Python Script Wrapper

```python
import subprocess

# Run ingestion
subprocess.run(["python", "cli_ingest.py", "--skip-confirm"])

# Run query
result = subprocess.run(
    ["python", "cli_query.py", "question?"],
    capture_output=True,
    text=True
)
print(result.stdout)
```

### Makefile

```makefile
.PHONY: ingest query ingest-verbose query-interactive

ingest:
	python cli_ingest.py

ingest-verbose:
	python cli_ingest.py -v

query:
	python cli_query.py -i

query-verbose:
	python cli_query.py -i -v
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Script not executable | `chmod +x cli_ingest.py cli_query.py` |
| Python not found | Use full path: `/usr/bin/python3 cli_ingest.py` |
| Module import errors | Ensure you're in RAG-pipeline directory |
| API key errors | Check .env file has all required keys |
| Port conflicts | Flask might be running; use different port or stop Flask |

---

## Quick Reference

```bash
# Ingest all PDFs
python cli_ingest.py

# Ingest specific file
python cli_ingest.py -f document.pdf

# Query (single)
python cli_query.py "Your question?"

# Query (interactive)
python cli_query.py -i

# Verbose mode
python cli_ingest.py -v
python cli_query.py "question?" -v

# Custom results
python cli_query.py "question?" -k 5

# Skip confirmations
python cli_ingest.py --skip-confirm
```

---

## Related Documentation

- [QUICK_START.md](QUICK_START.md) - 3-step setup
- [END_TO_END_GUIDE.md](END_TO_END_GUIDE.md) - Complete architecture
- [main.py](main.py) - Interactive menu system
- [app.py](app.py) - Flask REST API

