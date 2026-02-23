---
description: Integrate phase - test adapters with real infrastructure via Docker
---

1. Ensure all services are up: `./dev.sh up -d`.
2. Run integration tests targeting external services (Minio, Chroma, Redis).
3. Verify Celery task execution via `./dev.sh logs celery-worker`.
4. Use `orchestrator` for automated verification.
