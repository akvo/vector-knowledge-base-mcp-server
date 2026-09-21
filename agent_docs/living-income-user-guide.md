# User Guide: Living Income Data Pipeline

## Overview
The `kb_init_living_income.py` script is used to ingest local PDF documents into the Akvo RAG Knowledge Base.

## Prerequisites
- Python 3.11+
- Virtual environment with `requests` and `pandas` installed (e.g., `multimodal-rag-env`).

## Configuration
The script uses the following environment variables (sourced from `.env` or set manually):
- `ADMIN_API_KEY`: The master key for the RAG backend (default: "changeme").
- `RAG_MAIN_URL`: The URL of the RAG API (default: `http://main:8000/api/v1/`).

## Usage

### 1. Dry Run
Verify that the script can find the documents without uploading them:
```bash
./dev.sh exec script python -m kb_init_living_income --dry-run
```

### 2. Full Import
Run the script as a module inside the container:
```bash
./dev.sh exec script python -m kb_init_living_income
```

### 3. Custom Chunk Size
```bash
./dev.sh exec script python -m kb_init_living_income --chunk-size 5
```

## Troubleshooting
- **Connection Errors**: Ensure `RAG_MAIN_URL` is correct and pointing to a reachable service.
- **Auth Errors**: Verify `ADMIN_API_KEY` matches the backend configuration.
