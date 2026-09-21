---
description: Integrate phase - test adapters with real infrastructure
---

# Phase 3: Integrate (Vector KB MCP Stack)

## Purpose

Verify that adapter implementations (PostgreSQL, MinIO, ChromaDB, RabbitMQ/Celery, OpenAI) interact correctly with real containerized infrastructure.

## Prerequisites

- **Phase 2 (Implement)** completed with unit tests passing.
- Infrastructure running and accessible via `./dev.sh`.

## When Required

- Any code involving database persistence (PostgreSQL / Alembic migrations).
- Document upload and object storage (MinIO).
- Vector indexing and retrieval (ChromaDB).
- Message queues and background tasks (RabbitMQ & Celery).

## Steps

### 1. Setup Integration Environment

Ensure all required services are running:

```bash
./dev.sh up -d
./dev.sh ps
```

### 2. Integration Testing

Run tests that interact with real services:

- Verify database migrations and schema updates.
- Test ChromaDB vector search and embedding indexing.
- Test MinIO document upload and public bucket policy.

### 3. API & MCP Contract Verification

Verify that API and MCP tools satisfy their contracts:

- Check generated API documentation (`/api/docs`).
- Run FastMCP and E2E tests (`./dev.sh exec main ./test.sh mcp` and `./dev.sh exec main ./test.sh e2e`).

### 4. Manual Verification & Telemetry Sync

- Verify behavior under real network/data conditions.
- Inspect Celery worker status via Flower (`http://localhost:5556` dev / `5555` prod) or `./dev.sh logs celery-worker`.

## Development Commands

```bash
# Run MCP Integration / Tool Tests
./dev.sh exec main ./test.sh mcp

# Run End-to-End Tests
./dev.sh exec main ./test.sh e2e

# Test Specific Pipeline Script
./dev.sh exec script python -m kb_init_living_income
```

## Completion Criteria

- [ ] Integration and E2E tests passing for all components.
- [ ] Database migrations applied cleanly (`alembic upgrade head`).
- [ ] Environment variables and secrets handled securely.
- [ ] No major regressions in performance or connectivity.

## Next Phase

Proceed to **Phase 4: Verify** (`/4-verify`).
