# PRD: Living Income Data Pipeline

## 1. Introduction
The Akvo RAG system requires a new Knowledge Base (KB) for Living Income data. Instead of web scraping, the data is already available locally.

## 2. Requirements

### 2.1 Functional Requirements
- **FR1**: Script shall read all PDF files from `./script/downloads/living_income`.
- **FR2**: Script shall allow the user to specify the target environment (local vs. remote) and authentication.
- **FR3**: Script shall create a new Knowledge Base named "Living Income".
- **FR4**: Script shall upload documents in chunks to the RAG backend.
- **FR5**: Script shall trigger processing for the uploaded documents.

### 2.2 Technical Requirements
- Language: Python 3.11+
- Dependencies: `requests`, `pandas` (reusing pattern from `kb_init_tdt.py`).
- API Integration: Reuse `utils.api_util`.

## 3. User Acceptance Criteria (UAC)
- As a user, I can run `python script/kb_init_living_income.py` and see the documents being uploaded to the RAG server.
- The documents should be searchable in the Akvo RAG chat agent after processing.

## 4. Constraints
- Only process `.pdf` files.
- Scripts must be placed in the `script/` directory.
