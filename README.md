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
  - [🔑 Authentication](#-authentication)
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

DATABASE_URL=postgresql://akvo:password@db:5432/kb_mcp

# MinIO settings
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=documents

# Chroma DB settings
CHROMA_DB_HOST=chromadb
CHROMA_DB_PORT=8000

# OpenAI settings
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDINGS_MODEL=text-embedding-ada-002

```

**Notes**
- `APP_ENV` accepts two values: `prod` or `dev`.
- This variable controls the startup command in `entrypoint.sh`, determining whether the application runs in reload mode (`dev`) or in production mode (`prod`).

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
   ```bash
   ./dev.sh exec main ./test.sh
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

## 🔑 Authentication

All protected routes require an API Key.

Requests must include the API key in the `Authorization` header:

```http
Authorization: API-Key <your_api_key>
```

Example:
```bash
curl -X GET http://localhost:8100/api/v1/knowledge-base \
  -H "Authorization: API-Key sk_test_xxxxxxx"
```
👉 See SECURITY.md


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
```

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