---
description: Integrate phase - test adapters with real infrastructure via Docker
---

1. Ensure all services are up: `./dc.sh up -d`.
2. Run integration tests targeting external services (Minio, Chroma, Redis).
3. Verify Celery task execution via `./dc.sh logs worker`.
4. Use `orchestrator` for automated verification.
