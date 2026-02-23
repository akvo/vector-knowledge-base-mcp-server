# API Documentation: Vector Knowledge Base MCP Server

## Authentication

All API requests (except health checks) require an API Key passed in the `Authorization` header.

### Admin API Key
- Header: `Authorization: Admin-Key <your_admin_api_key>`
- Used for: Managing API keys (creation, activation, deactivation).

### User/API Key
- Header: `Authorization: API-Key <your_api_key>`
- Used for: Accessing Knowledge Base and Document endpoints.

### Target API URL (Optional)
- Environment Variable: `RAG_MAIN_URL`
- Default: `http://main:8000/api/v1/`
- Used for: Overriding the backend API endpoint for internal scripts.

---

## Knowledge Base (KB) Endpoints

### List Knowledge Bases
- **GET** `/api/v1/knowledge-base`
- Retrieve a list of all accessible knowledge bases.

### Create Knowledge Base
- **POST** `/api/v1/knowledge-base`
- Create a new logical grouping for documents and vectors.

---

## Document Endpoints

### Standard Document Upload
- **POST** `/api/v1/document`
- Upload a file to MinIO and create a database record.

### Full Process Upload (Recommended)
- **POST** `/api/v1/document/process`
- Upload, chunk, and embed a document in a single request. Dispatches background Celery tasks.

---

## Retrieval Endpoints

### Similarity Search
- **POST** `/api/v1/retrieval/query`
- Perform a similarity search across one or more knowledge bases. returns context chunks and metadata.

---

## MCP Server

### Connection Info
- **Endpoint**: `/mcp`
- **Protocol**: HTTP (SSE/Stateless compatible)

### Available Tools
- `greeting(name: str)`: Returns a hello message.
- `query_knowledge_base(query: str, knowledge_base_ids: List[int], top_k: int = 10)`: The primary tool for AI models to query the knowledge base.
