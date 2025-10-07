#!/usr/bin/env bash
set -euo pipefail

APP_ENV=${APP_ENV:-prod}
HOST=0.0.0.0
PORT=8000
DATABASE_URL=${DATABASE_URL}

echo "📦 Environment: $APP_ENV"
echo "📡 FastAPI Host: $HOST"
echo "🔌 FastAPI Port: $PORT"

if ! command -v psql >/dev/null 2>&1; then
    echo "❌ psql not found! Please install postgresql-client in your Dockerfile"
    exit 1
fi

# Wait for Postgres
echo "⏳ Waiting for Postgres..."
until psql "$DATABASE_URL" -c '\q' 2>/dev/null; do
    echo "   Postgres not ready yet..."
    sleep 2
done
echo "✅ Postgres is ready!"

# Run migrations
echo "🗄️ Running migrations..."
if alembic upgrade head; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

# --- START SERVER ---
if [ "$APP_ENV" = "dev" ]; then
    echo "🔧 Starting in development mode..."
    uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --timeout-keep-alive 300
else
    echo "🚀 Starting in production mode (optimized for long-lived MCP streams)..."
    uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers 2 \
        --timeout-keep-alive 300 \
        --graceful-timeout 60 \
        --limit-max-requests 1000 \
        --log-level info
fi