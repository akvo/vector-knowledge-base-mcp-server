# Docker Commands

**All commands MUST be executed via `./dev.sh`. Never run bare commands outside Docker.**

## Environment Management

```bash
./dev.sh up -d           # Start all services
./dev.sh down            # Stop all services
./dev.sh ps              # View running services
./dev.sh logs -f         # Follow all logs
./dev.sh logs main       # View specific service logs
./dev.sh build           # Rebuild services
```

## Backend Commands (FastAPI)

```bash
./dev.sh exec main bash                          # Open shell in main container
./dev.sh exec main uvicorn app.main:app --host 0.0.0.0 --reload # Run app manually (inside container)
./dev.sh exec main ./test.sh all                 # Run all tests
./dev.sh exec main pip install <package>         # Install dependencies
```

## Data Pipeline & Scripts

```bash
./dev.sh exec script python -m kb_init_unep         # Run UNEP import
./dev.sh exec script python -m kb_init_tdt          # Run TDT import
./dev.sh exec script python -m kb_init_living_income # Run Living Income import
```
```

## AI & Data Services

```bash
./dev.sh logs chromadb                          # View ChromaDB logs
./dev.sh logs minio                             # View Minio logs
./dev.sh logs celery-worker                     # View Celery worker logs
./dev.sh logs celery-beat                       # View Celery beat logs
./dev.sh logs flower                            # View Flower (task monitor) logs
```

## Rules

1. **Never run `python`, `pip`, or `pytest` directly** — always prefix with `./dev.sh exec main` or `./dev.sh exec script`.
2. **Hot reload** is enabled for the `main` service via volume mounting in dev mode.
3. **Environment variables** go in `.env` file.
