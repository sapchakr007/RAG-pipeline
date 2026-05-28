# Intelligent Multi-Bank RAG & Statement Pipeline Skill

A reusable instruction sheet for AI coding assistants to manage, query, and scale the end-to-end multi-bank document processing and React/Flask dashboard system.

---

## 🎯 Objectives & Capabilities

This skill instructs the agent on how to:
1. **Idempotently Ingest Statements**: Scan new PDFs in `data/`, verify MD5 checksum hashes, and index only new files.
2. **Execute Multi-Bank Parsing Heuristics**: Process structured tables from diverse bank layouts (Kotak Bank and ICICI Bank).
3. **Query pinecone Database**: Perform RAG semantic searches over processed financial fragments.
4. **Boot Up & Maintain Web UI**: Launch the Flask backend API and the React frontend dashboard under unified ports.

---

## 🛠️ Operational Workflows

### 1. Ingestion & Delta Loading
To parse new bank statement PDFs in the `data/` directory without duplication:
```bash
python cli_ingest.py
```
- **State Files**:
  - Ingested files and MD5 checksum hashes are tracked in [processed_pdfs.json](file:///Users/sapchakrab/documents/github/RAG-pipeline/data/processed_pdfs.json).
  - Structured records are appended to [transactions.json](file:///Users/sapchakrab/documents/github/RAG-pipeline/data/transactions.json).
- **Reset Ingestion**: To force a re-ingestion of existing PDFs, delete the key-value tracking in `processed_pdfs.json` and clear `transactions.json`.

### 2. RAG Semantic Querying CLI
To ask analytical questions directly over the vectorized database:
```bash
python cli_query.py --query "what are the transactions on swiggy?"
```

### 3. Launching the Web UI Dashboard
To boot up both servers simultaneously in a background task:
```bash
python launch_web_ui.py
```
- **Backend API**: Serves on [http://localhost:5001](http://localhost:5001)
- **Frontend React**: Serves on [http://localhost:3000](http://localhost:3000)

---

## 🦁 Multi-Bank Parsing Heuristics (Crucial Context)

When parsing new PDF statement text extracts inside [transaction_extractor.py](file:///Users/sapchakrab/documents/github/RAG-pipeline/src/transaction_extractor.py), be mindful of these unique layout rules:

### A. Kotak Mahindra Debit Statement
- Standard row-by-row layout.
- Parses dates like `DD-MMM-YYYY` (e.g. `29-Apr-2026`).
- Identifies spends via standard transaction lines and maps category keywords deterministic.

### B. ICICI Credit Card MITC Statement (Single-Line Challenge)
- PyPDF2 extracts this card statement text as a **single, squashed continuous line** (lacking vertical formatting or newlines).
- **Header Matcher**: Check for text dense with `DateSerNo.Transaction Details` or multi-date slashes to activate relaxed single-line parsing mode.
- **Line Splitting**: Split the continuous string at every date marker occurrence (`\d{2}/\d{2}/\d{4}`).
- **Amount & Points Separator (`_parse_icici_amount`)**: Reward points are often merged directly with decimal transaction values (e.g. `10515.00` representing `10` reward points and `515.00` spend). Evaluate trailing decimals and comma delimiters to parse actual spend thresholds cleanly.

---

## 🔍 Troubleshooting Guide

### 1. Flask backend Import Issues
If Flask fails to serve `/api/transactions` due to unresolved references, ensure `import json` and `from pathlib import Path` are present at the top of [app.py](file:///Users/sapchakrab/documents/github/RAG-pipeline/app.py).

### 2. Web UI Launcher Process Cleanups
If the launcher script warns that port 5001 or 3000 is in use, terminate active tasks or run:
```bash
kill -9 $(lsof -t -i:5001)
kill -9 $(lsof -t -i:3000)
```

### 3. CSS Syntax Compilation Warnings
If Webpack fails with an `Unclosed block` inside `RAGInterface.css` or `TransactionTable.css`, check for unclosed hover/animation brackets (`}`) in the stylesheets.

---
