# PRD: Vector Knowledge Base MCP Server

## 1. Goal
Implement a robust Model Context Protocol (MCP) server for managing and querying a vector-based knowledge base.

## 2. Target Features
- **Semantic Search & Retrieval**: Ability to perform vector-based similarity searches and retrieve context-aware answers via `retrieval_router`.
- **Knowledge Base Management**: CRUD operations for logical knowledge base groupings via `kb_router`.
- **Advanced Document Processing**:
    - Standard CRUD operations via `document_router`.
    - Integrated processing (upload, chunk, embed) via `document_full_process_router`.
    - Support for multiple document formats using `document_processor` and `celery` tasks.
- **Secure API & MCP**:
    - Two-tier authentication (Admin-Key, API-Key).
    - Hardened `SecureFastMCP` implementation with custom middleware.
    - Expose `query_knowledge_base` and `greeting` tools to MCP clients.
- **Browser-Viewable Documents**: Direct access to MinIO-stored documents through Nginx proxy.

## 3. Tech Stack
- **Framework**: FastAPI (Backend), FastMCP (MCP)
- **Vector Store**: ChromaDB
- **Object Storage**: MinIO
- **Relational DB**: PostgreSQL (RDS compatible)
- **Task Queue**: Celery with Redis/PostgreSQL (for background document processing)
- **Proxy**: Nginx
- **Containerization**: Docker Compose

## 4. Technical Requirements
- **Async I/O**: Use `async` for all I/O-bound operations.
- **Persistence**: Ensure data persists across container restarts.
- **Security**: Implement API key authentication for all Knowledge Base endpoints.
- **Observability**: Health checks for all services.

## 5. Success Metrics
- Successful deployment via `docker compose`.
- 100% test pass rate for API and MCP endpoints.
- Retrieval latency under 500ms for standard queries.
