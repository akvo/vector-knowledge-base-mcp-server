# 📚 Table of Contents

- [📚 Table of Contents](#-table-of-contents)
- [🤖 UNEP Knowledge Base import script](#-unep-knowledge-base-import-script)
  - [🔐 Environment Variables](#-environment-variables)
  - [🚀 Running the Script](#-running-the-script)
  - [📁 Directory Structure](#-directory-structure)
- [🤖 TDT Knowledge Base import script](#-tdt-knowledge-base-import-script)
  - [🔐 Environment Variables](#-environment-variables-1)
  - [🚀 Running the Script](#-running-the-script-1)
  - [📁 Directory Structure](#-directory-structure-1)
- [🤖 Living Income Knowledge Base import script](#-living-income-knowledge-base-import-script)
  - [🔐 Environment Variables](#-environment-variables-2)
  - [🚀 Running the Script](#-running-the-script-2)
  - [📁 Directory Structure](#-directory-structure-2)

---

# 🤖 UNEP Knowledge Base import script

This script automates the process of collecting, saving, and uploading PDF documents from [GlobalPlasticsHub](https://globalplasticshub.org) into a Vector Knowledge Base MCP Server.

This Python script supports three main operation modes:

1. **CSV Only** – Save PDF URLs to a CSV file.
2. **CSV + Download** – Save URLs and download the corresponding PDFs.
3. **Full Process** – Save URLs, download PDFs, and upload/process them into Vector Knowledge Base MCP Server.

## 🔐 Environment Variables

Before running the script, set `ADMIN_API_KEY` credentials in your shell or environment:

``` bash
export ADMIN_API_KEY="your-admin-api-key-here"
```

The `ADMIN_API_KEY` is currently used for authentication to access the CRUD API keys endpoint. With this, the script can create an API key that will be used as the authentication token to access the CRUD Knowledge Base.

👉 [How to generate `ADMIN_API_KEY`](../GENERATE_ADMIN_API_KEY.md)

## 🚀 Running the Script

To execute the script:

```bash
./dev.sh exec script python -m kb_init_unep
```

You will be prompted to:
- Choose the operation mode:
  1: Save PDF URLs to CSV only.
  2: Save to CSV and download PDFs.
  3: Full process (CSV + download + upload to Vector Knowledge Base MCP Server).

- Enter the number of documents to import.
- Provide a description for the knowledge base.

## 📁 Directory Structure
```bash
./downloads/unep/unep_files.csv – Stores PDF URLs and offsets.
./downloads/unep/ – Folder where downloaded PDF files are saved.
```

---

# 🤖 TDT Knowledge Base import script

This script automates the process of collecting, saving, and uploading PDF documents from [TDT Knowledge Hub](https://tdt.akvotest.org/knowledge-hub) into a Vector Knowledge Base MCP Server.

This Python script supports three main operation modes:

1. **CSV Only** – Save PDF URLs to a CSV file.
2. **CSV + Download** – Save URLs and download the corresponding PDFs.
3. **Full Process** – Save URLs, download PDFs, and upload/process them into Vector Knowledge Base MCP Server.

## 🔐 Environment Variables

Before running the script, set `ADMIN_API_KEY` credentials in your shell or environment:

``` bash
export ADMIN_API_KEY="your-admin-api-key-here"
```

## 🚀 Running the Script

To execute the script:

```bash
./dev.sh exec script python -m kb_init_tdt
```

You will be prompted to:
- Choose the operation mode:
  1: Save PDF URLs to CSV only.
  2: Save to CSV and download PDFs.
  3: Full process (CSV + download + upload to Vector Knowledge Base MCP Server).

- Enter the number of documents to import.
- Provide a description for the knowledge base.

## 📁 Directory Structure
```bash
./downloads/tdt/tdt_files.csv – Stores PDF URLs and offsets.
./downloads/tdt/ – Folder where downloaded PDF files are saved.
```

---

# 🤖 Living Income Knowledge Base import script

This script automates the ingestion of local Living Income PDF documents into the Vector Knowledge Base MCP Server.

## 🔐 Environment Variables

Before running the script, ensure `ADMIN_API_KEY` is set in your `.env` file or environment. You can also override the target API URL using `RAG_MAIN_URL`.

``` bash
export ADMIN_API_KEY="your-admin-api-key-here"
export RAG_MAIN_URL="http://main:8000/api/v1/"
```

## 🚀 Running the Script

To execute the script as a module inside the Docker container:

```bash
./dev.sh exec script python -m kb_init_living_income
```

Optional arguments:
- `--dry-run`: List files without uploading.
- `--chunk-size`: Number of files per upload batch (default: 10).

## 📁 Directory Structure
```bash
./downloads/living_income/ – Folder containing the source PDF files.
```
