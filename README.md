# Vector Knowledge Base MCP Server

[![Repo Size](https://img.shields.io/github/repo-size/akvo/vector-knowledge-base-mcp-server)](https://img.shields.io/github/repo-size/akvo/vector-knowledge-base-mcp-server) [![Languages](https://img.shields.io/github/languages/count/akvo/vector-knowledge-base-mcp-server)](https://img.shields.io/github/languages/count/akvo/vector-knowledge-base-mcp-server) [![Issues](https://img.shields.io/github/issues/akvo/vector-knowledge-base-mcp-server)](https://img.shields.io/github/issues/akvo/vector-knowledge-base-mcp-server) [![Last Commit](https://img.shields.io/github/last-commit/akvo/vector-knowledge-base-mcp-server/main)](https://img.shields.io/github/last-commit/akvo/vector-knowledge-base-mcp-server/main)

A high-performance FastAPI/FastMCP-based Model Context Protocol (MCP) server that provides vector-based knowledge management with document storage, similarity search, and intelligent retrieval capabilities.

---

## 📖 Table of Contents

- [Vector Knowledge Base MCP Server](#vector-knowledge-base-mcp-server)
  - [📖 Table of Contents](#-table-of-contents)
  - [🚀 Features](#-features)
  - [🏗️ Architecture](#️-architecture)
  - [🛠️ Tech Stack](#️-tech-stack)
  - [📋 Prerequisites](#-prerequisites)
  - [🚀 Quick Start](#-quick-start)
    - [Environment Variables](#environment-variables)
    - [Development Setup](#development-setup)
    - [Production Setup](#production-setup)
    - [Service Ports (dev)](#service-ports-dev)
  - [🔑 Authentication and API Keys](#-authentication-and-api-keys)
    - [Using the Admin API Key](#using-the-admin-api-key)
    - [Using the API Key](#using-the-api-key)
    - [Summary Table](#summary-table)
  - [📦 MinIO Document Storage and Public Access](#-minio-document-storage-and-public-access)
    - [How It Works](#how-it-works)
    - [Configuration](#configuration)
    - [Document URLs](#document-urls)
    - [Security Considerations](#security-considerations)
  - [📖 API Documentation](#-api-documentation)
  - [📁 Project Structure](#-project-structure)
  - [🚨 Troubleshooting](#-troubleshooting)
    - [Health Checks](#health-checks)
  - [🤝 Contributing](#-contributing)
    - [Development Guidelines](#development-guidelines)
  - [📄 License](#-license)
  - [🆘 Support](#-support)

---

## 🚀 Features

- FastAPI Backend: High-performance async API server
- Vector Database: ChromaDB integration for semantic search
- Document Storage: MinIO object storage for file management
- PostgreSQL Database: Structured data storage and metadata
- MCP Protocol: Model Context Protocol server implementation using FastMCP
- Admin Interface: PgAdmin for database management (development only)
- Development Ready: Hot-reload and development tools included

## 🏗️ Architecture

```bash
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│   ChromaDB      │────│   PostgreSQL    │
│   (Port 8100)   │    │   (Port 8101)   │    │   (Port 5432)   │
│─────────────────│    └─────────────────┘    └─────────────────┘
│   FastMCP App   │
│ (Port 8100/mcp) │
└─────────────────┘
         │
         │
┌─────────────────┐    ┌─────────────────┐
│     MinIO       │    │    PgAdmin      │
│ (Ports 9100/01) │    │   (Port 5550)   │
└─────────────────┘    └─────────────────┘
```

*All port described in above schema are for development*

## 🛠️ Tech Stack

- Backend: FastAPI with Python 3.11+
- Vector Database: ChromaDB for embeddings and similarity search
- Database: PostgreSQL 12 with Alpine Linux
- Object Storage: MinIO for file storage
- Containerization: Docker & Docker Compose
- MCP Protocol: FastMCP for model context protocol implementation

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

## 🚀 Quick Start

### Environment Variables

Before running the application, create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Fill in the variables according to your environment:

```env
APP_ENV=dev
APP_PORT=8100

# Nginx
NGINX_PORT=8080

DATABASE_URL=postgresql://akvo:password@db:5432/kb_mcp

# MinIO settings
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=documents
# Should be same as NGINX_PORT
MINIO_SERVER_URL=http://localhost:8080/minio

# Chroma DB settings
CHROMA_DB_HOST=chromadb
CHROMA_DB_PORT=8000
VECTOR_STORE_BATCH_SIZE=100

# OpenAI settings
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDINGS_MODEL=text-embedding-ada-002

# Admin Auth
ADMIN_API_KEY=your-admin-api-key-here
```

**Notes**
- `APP_ENV` accepts two values: `prod` or `dev`.
- This variable controls the startup command in `entrypoint.sh`, determining whether the application runs in reload mode (`dev`) or in production mode (`prod`).
- `VECTOR_STORE_BATCH_SIZE` controls how many documents are processed in a single batch when adding to the vector store. There is a trade off between performance and hitting limits on the number of chunks that can be stored at once default is 100 but you can tune this setting here.
- `ADMIN_API_KEY` currently used for authentication to access the CRUD API keys endpoint. With this, the script can create an API key that will be used as the authentication token to access the CRUD Knowledge Base.
  - 👉 [How to generate `ADMIN_API_KEY`](./GENERATE_ADMIN_API_KEY.md)
- `MINIO_ENDPOINT` is the internal Docker network address used by the FastAPI application to communicate with MinIO.
- `MINIO_SERVER_URL` is the external URL that browsers use to access documents through the Nginx proxy. It should match your `NGINX_PORT`.

### Development Setup

1. **Clone the repository**
   ```bash
   git clone git@github.com:akvo/vector-knowledge-base-mcp-server.git
   cd vector-knowledge-base-mcp-server
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

3. **Start the development environment**
   ```bash
   ./dev.sh up -d
   ```

4. **Verify services are running**
   ```bash
   docker compose ps
   ```

5. **Running pytest**
   - Running FastAPI endpoint test

   ```bash
   ./dev.sh exec main ./test.sh api
   ```

   - Running e2e test

   ```bash
   ./dev.sh exec main ./test.sh e2e
   ```
   - Running FastMCP test

   ```bash
   ./dev.sh exec main ./test.sh mcp
   ```

   - Running All test

   ```bash
   ./dev.sh exec main ./test.sh all
   ```

### Production Setup

1. **Build and start production services**
   ```bash
   docker compose -f docker-compose.yml up -d
   ```

### Service Ports (dev)

| Service | Development | Production | Description |
|---------|-------------|------------|-------------|
| FastAPI | 8100 | 8000 | Main application API |
| ChromaDB | 8101 | 8001 | Vector database |
| PostgreSQL | 5432 | 5432 | Primary database |
| MinIO API | 9100 | 9000 | Object storage API |
| MinIO Console | 9101 | 9001 | MinIO web interface |
| PgAdmin | 5550 | - | Database admin (dev only) |
| Nginx | 8080 | 80 | Reverse proxy |

## 🔑 Authentication and API Keys

This project uses **API keys** for authentication to access the Knowledge Base and Admin APIs. There are two types of keys:
1. **Admin API Key** (`ADMIN_API_KEY`) – Used for administrative actions, such as creating or revoking other API keys.
2. **API Key** – Generated via the Admin API to access the Knowledge Base endpoints.

### Using the Admin API Key

- Your `ADMIN_API_KEY` is defined in your `.env` file.
- To perform administrative tasks, include it in the `Authorization` header:

```http
Authorization: Admin-API-Key <your_admin_api_key>
```

**Example: Create a new API key via Admin endpoint**

```bash
curl -X POST http://localhost:8100/api/v1/api-key \
  -H "Authorization: Admin-Key sk_xxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"name": "app-name", "is_active": true}'
```

### Using the API Key

- The generated API key is used to access protected Knowledge Base endpoints.
- Include it in the `Authorization` header:

```http
Authorization: API-Key <your_api_key>
```

**Example: Query the Knowledge Base**

```bash
curl -X GET http://localhost:8100/api/v1/knowledge-base \
  -H "Authorization: API-Key sk_xxxxxxx"
```
👉 For the detail of `API-Key` usage, please read: SECURITY.md

### Summary Table

| Key Type      | Header Name                          | Purpose                                    |
| ------------- | ------------------------------------ | ------------------------------------------ |
| Admin API Key | `Authorization: Admin-Key <key>` | Manage API keys and administrative tasks   |
| User/API Key  | `Authorization: API-Key <key>`       | Access Knowledge Base and perform CRUD ops |

## 📦 MinIO Document Storage and Public Access

This application uses MinIO for object storage and provides public access to uploaded documents through an Nginx reverse proxy. This allows documents to be directly viewed or downloaded in web browsers without requiring AWS signature-based authentication.

### How It Works

The document access flow is designed to work seamlessly with Docker networking:

```
Browser Request
    ↓
http://localhost:8080/minio/documents/kb_1/file.pdf
    ↓
Nginx (port 8080) - Reverse Proxy
    ↓
MinIO Container (minio:9000) - Internal Docker Network
    ↓
Document Served
```

**Key Components:**

1. **Internal Communication (`MINIO_ENDPOINT`)**:
   - Used by FastAPI application for upload, delete, and management operations
   - Format: `minio:9000`
   - Only accessible within Docker network

2. **External Access (`MINIO_SERVER_URL`)**:
   - Used by browsers to access documents
   - Format: `http://localhost:8080/minio`
   - Routed through Nginx reverse proxy

3. **Public Bucket Policy**:
   - The MinIO bucket is configured with a public read policy
   - Allows direct document access without AWS signatures
   - Policy version `2012-10-17` is the AWS S3 standard (static, never changes)

### Configuration

**Environment Variables:**

```env
# Internal endpoint - used by FastAPI for operations
MINIO_ENDPOINT=minio:9000

# External endpoint - used by browsers to access files
MINIO_SERVER_URL=http://localhost:8080/minio

# MinIO credentials
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=documents
```

**Nginx Configuration:**

The Nginx proxy is configured to forward `/minio/*` requests to the MinIO service:

```nginx
location /minio/ {
    proxy_pass http://minio/;
    proxy_set_header Host $host;
    # ... additional proxy settings
}
```

### Document URLs

When a document is uploaded and processed, the API returns URLs in this format:

```json
{
  "document_id": 1,
  "file_name": "example.pdf",
  "file_path": "http://localhost:8080/minio/documents/kb_1/example.pdf",
  "file_type": "application/pdf",
  "is_viewable_in_browser": true
}
```

These URLs can be:
- Opened directly in a browser
- Embedded in `<iframe>` elements
- Used in PDF viewers
- Downloaded via direct links

### Security Considerations

**Current Setup:**
- Documents in the knowledge base are publicly readable
- No authentication required for document access
- Suitable for internal networks or non-sensitive data

**For Production with Sensitive Data:**

If you need to restrict document access, consider:

1. **API-based Access**: Remove public bucket policy and stream documents through authenticated API endpoints
2. **Nginx Authentication**: Add authentication at the Nginx level
3. **Network Isolation**: Keep MinIO and Nginx on a private network
4. **VPN/Firewall**: Restrict access to authorized networks only

**To disable public access**, remove or modify the bucket policy in `minio_service.py`:

```python
# Comment out or remove this in init_minio()
# set_bucket_public_read_policy(bucket_name)
```

Then implement authentication at the API or Nginx level based on your security requirements.

## 📖 API Documentation

Once the application is running `(uvicorn app.main:app --reload` or via Docker), the API documentation is automatically available through **FastAPI docs**:
- Swagger UI → http://localhost:8000/api/docs or http://localhost:8100/api/docs
- ReDoc → http://localhost:8000/redoc or http://localhost:8100/redoc

From these interfaces, you can:
- Try out endpoints directly
- View request and response schemas
- Test the API interactively

## 📁 Project Structure

```bash
vector-knowledge-base-mcp-server/
├── main/                          # FastAPI application
│   ├── app/
│   │   ├── api/                   # API routes (endpoint FastAPI)
│   │   ├── core/                  # Core configuration (settings, logging, security)
│   │   ├── mcp/                   # MCP related files (FastMCP server, tools)
│   │   ├── models/                # Pydantic models / ORM models
│   │   ├── schemas/               # API schemas (Pydantic / base)
│   │   ├── services/              # Business logic / service layer
│   │   ├── utils/                 # Helpers / utilities
│   ├── tests/                     # Unit / integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── nginx/                         # Nginx reverse proxy
│   ├── conf.d/
│   │   └── default.conf          # Nginx configuration
│   └── Dockerfile
├── db/
│   ├── docker-entrypoint-initdb.d/ # Init SQL scripts
│   └── script/                    # Migration / seed
├── pgadmin4/
│   └── servers.json               # GUI config
├── docker-compose.yml             # Compose prod
├── docker-compose.override.yml    # Override dev
├── .env.example                   # Env vars
└── README.md
```

## 🚨 Troubleshooting

### Health Checks

```bash
# Check all services
curl http://localhost:8100/health

# Check individual components
curl http://localhost:8101/api/v2/heartbeat  # ChromaDB
curl http://localhost:9100/minio/health/live # MinIO
curl http://localhost:8080/health            # Nginx
```

**Common Issues:**

1. **Cannot access documents (404 error)**
   - Verify Nginx is running: `docker compose ps nginx`
   - Check Nginx logs: `docker compose logs nginx`
   - Ensure `MINIO_SERVER_URL` matches your `NGINX_PORT`

2. **MinIO connection refused**
   - Verify MinIO is running: `docker compose ps minio`
   - Check MinIO logs: `docker compose logs minio`
   - Ensure bucket policy is set correctly (check application logs during startup)

3. **Documents not loading in browser**
   - Check if URL format is correct: `http://localhost:8080/minio/documents/...`
   - Verify bucket policy: Access MinIO console at `http://localhost:9101` and check bucket permissions
   - Review Nginx proxy configuration in `nginx/conf.d/default.conf`

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation for API changes
- Use conventional commits for commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Open an issue on GitHub
- **Documentation**: Check the `/docs` endpoint when server is running
- **Community**: Join our discussions in GitHub Discussions

---

**Built with ❤️ using FastAPI and FastMCP**