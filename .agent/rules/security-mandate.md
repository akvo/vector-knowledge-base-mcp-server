# Security Mandate

**Security is a foundational requirement, not a feature.**

## Universal Security Principles

1. **Never trust user input**: All data from users, APIs, or external sources must be validated server-side.
2. **Deny by default**: Require explicit permission grants.
3. **Fail securely**: Fail closed (deny access) rather than open.
4. **Defense in depth**: Multiple layers of security.

## FastAPI & AI Specifics

- **Input Validation**: Use Pydantic models for all request bodies.
- **LLM Safety**: Sanitize and validate LLM outputs before using them in sensitive operations.
- **Environment Variables**: Store API keys (OpenAI, Anthropic, etc.) and database secrets in `.env`, never hardcode.
- **Minio Access**: Use signed URLs for accessing objects in Minio.
- **Chroma Auth**: Ensure Chroma server is not exposed publicly without authentication or network isolation.
- **Dependency Vetting**: Regularly check `requirements.txt` for known vulnerabilities.
