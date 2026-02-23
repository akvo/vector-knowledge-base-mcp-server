# FastAPI Backend Rules

Follow these standards for all Python backend code in this stack.

## API Design

1. **Pydantic Models**: Use Pydantic models for request validation and response serialization.
2. **Dependency Injection**: Use FastAPI's `Depends` for shared logic like authentication or database sessions.
3. **Structured Response**: Ensure all API responses follow a consistent format (e.g., success/error objects).
4. **Asynchronous Code**: Prefer `async def` for endpoints and operations that involve I/O.

## Project Structure

- `app/api/`: Endpoint definitions.
- `app/models/`: Database or domain models.
- `app/schemas/`: Pydantic schemas.
- `app/services/`: Business logic and external service integrations.
- `app/mcp/`: MCP protocol server and tool definitions.
- `app/utils/`: Shared utility functions.
- `script/`: Data pipeline and initialization scripts.

## Testing

- Use `pytest` for all tests.
- Mock external services (Chroma, Minio, LLMs) in unit tests.
- Run integration tests against actual Docker containers when using the `/3-integrate` workflow.
