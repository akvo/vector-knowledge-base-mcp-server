#!/bin/bash
set -e

MODE=${1:-${CELERY_MODE:-worker}}
DATABASE_URL=${DATABASE_URL}

# --- Wait for Postgres to be ready ---
echo "⏳ Waiting for Postgres..."
until psql "$DATABASE_URL" -c '\q' 2>/dev/null; do
    echo "   Postgres not ready yet..."
    sleep 2
done
echo "✅ Postgres is ready!"


echo "Starting Celery in '$MODE' mode..."
if [ "$MODE" = "worker" ]; then
    celery -A app.celery_app worker --loglevel=INFO
    elif [ "$MODE" = "beat" ]; then
    celery -A app.celery_app beat --loglevel=INFO
else
    echo "Unknown CELERY_MODE: $MODE"
    exit 1
fi
