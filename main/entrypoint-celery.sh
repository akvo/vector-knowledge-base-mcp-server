#!/bin/bash
set -e

MODE=${CELERY_MODE:-worker}

echo "Starting Celery in '$MODE' mode..."

if [ "$MODE" = "worker" ]; then
    celery -A app.celery_app worker --loglevel=INFO
    elif [ "$MODE" = "beat" ]; then
    celery -A app.celery_app beat --loglevel=INFO
else
    echo "Unknown CELERY_MODE: $MODE"
    exit 1
fi
