# 🔒 Security Policy

This document describes how authentication and security are handled in the **Vector Knowledge Base MCP Server**.

---

## 📖 Table of Contents
- [🔒 Security Policy](#-security-policy)
  - [📖 Table of Contents](#-table-of-contents)
  - [📌 API Key Authentication](#-api-key-authentication)
    - [Header Format](#header-format)
  - [🔑 API Key Management](#-api-key-management)
  - [⚠️ Best Practices](#️-best-practices)

---

## 📌 API Key Authentication

All protected routes require a valid **API Key** to be provided in the `Authorization` header.

### Header Format

```http
Authorization: API-Key <your_api_key>
```

- `API-Key` is the required prefix.
- `<your_api_key>` must be replaced with the actual key value generated from the API key management endpoints.

Example:
```bash
curl -X GET http://localhost:8100/api/v1/knowledge-base \
  -H "Authorization: API-Key sk_test_xxxxxxx"
```

## 🔑 API Key Management

API Keys are managed via the `/api/v1/api-keys` endpoints:

- Create API Key
```http
POST /api/v1/api-keys
```

- List API Keys
```http
GET /api/v1/api-keys
```

- Update API Key
```http
PUT /api//v1/api-keys/{id}
```

- Delete API Key
```http
DELETE /api/v1/api-keys/{id}
```

Each key can be toggled active/inactive, and last usage is automatically updated on every request.

See [API docs](http://localhost:8100/api/docs#/) for the details.

## ⚠️ Best Practices

- Treat API keys like passwords:
  - Do not share them publicly or commit them to version control.
  - Rotate keys regularly.
  - Delete unused keys immediately.
- Use different API keys for different environments (development, staging, production).
- Restrict API key usage to secure connections (https).
