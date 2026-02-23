# AI Workflow Rules

Guidelines for implementing AI agents and RAG workflows using LangChain.

## LangChain RAG Orchestration

1. **Document Loading**: Support various formats (PDF, DOCX, TXT) using `pypdf` and `python-docx`.
2. **Chunking Strategy**: Use consistent chunking (e.g., recursive character text splitter) via `document_processor`.
3. **Embedding Persistence**: Ensure embeddings are stored in ChromaDB using `langchain-chroma`.
4. **Vector Search**: Use semantic similarity search with appropriate `top_k` filtering.

## LangChain Integration

1. **Prompt Templates**: Store prompts in separate files or as structured constants in `app/services/`.
2. **Tool Definition**: Use FastMCP `@mcp.tool` decorator for exposing tools to MCP clients.
3. **Model Configuration**: Use `langchain-openai` for model interactions, configured via `.env`.

## Vector Database (Chroma)

1. **Collection Naming**: Consistent naming convention for Chroma collections.
2. **Embedding Consistency**: Ensure the same embedding model is used for both ingestion and retrieval.

## Object Storage (Minio)

1. **Bucket Lifecycle**: Automated bucket creation on application startup if not exists.
2. **File References**: Store file keys in the database or agent state, not raw URLs.
