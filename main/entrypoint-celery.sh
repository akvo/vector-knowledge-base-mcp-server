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

# --- Wait for RabbitMQ to be ready ---
echo "⏳ Waiting for RabbitMQ..."
MAX_RETRIES=30
RETRY_COUNT=0

until timeout 5 bash -c "cat < /dev/null > /dev/tcp/${RABBITMQ_HOST}/${RABBITMQ_PORT:-5672}" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ RabbitMQ not ready after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "   RabbitMQ not ready yet (attempt $RETRY_COUNT/$MAX_RETRIES)..."
    sleep 2
done
echo "✅ RabbitMQ is ready!"

echo "Starting Celery in '$MODE' mode..."

if [ "$MODE" = "worker" ]; then
    # Add concurrency and max-tasks-per-child settings
    exec celery -A app.celery_app worker \
        --loglevel=INFO \
        --concurrency=4 \
        --max-tasks-per-child=1000 \
        --without-gossip \
        --without-mingle \
        --without-heartbeat

elif [ "$MODE" = "beat" ]; then
    exec celery -A app.celery_app beat \
        --loglevel=INFO

else
    echo "❌ Unknown CELERY_MODE: $MODE"
    echo "Valid modes: worker, beat"
    exit 1
fi