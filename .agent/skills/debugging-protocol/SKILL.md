---
name: debugging-protocol
description: Systematic protocol for debugging common issues in the FastAPI AI stack.
---

# Debugging Protocol

Follow these steps when encountering issues in the FastAPI AI stack.

## 1. Check Service Status

```bash
./dc.sh ps
```
Ensure all services (`app`, `worker`, `redis`, `minio`, `chroma`) are `running`.

## 2. Inspect Logs

- **App**: `./dc.sh logs app`
- **Worker**: `./dc.sh logs worker`
- **Chroma**: `./dc.sh logs chroma`

Look for tracebacks, connection errors, or LLM API timeouts.

## 3. Diagnose Common Issues

### Connection Errors
- **Redis**: Check if `REDIS_URL` matches the service name in `docker-compose.yml`.
- **Minio/Chroma**: Ensure the hostnames in the application configuration are `minio` and `chroma` respectively (Docker DNS).

### Celery Worker Issues
- If tasks are not executing, check if the worker is registered: `./dc.sh exec app celery -A app.core.celery_app inspect ping`.
- Verify the task name in the log matches the one called by the app.

### LangGraph Hangs
- Check for infinite loops in conditional edges.
- Verify LLM API limits and connectivity.

## 4. Run Tests

```bash
./dc.sh tests
```
Run tests to isolate the component failing.
