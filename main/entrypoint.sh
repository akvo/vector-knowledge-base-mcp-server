#!/usr/bin/env bash
set -euo pipefail

APP_ENV=${APP_ENV:-prod}
HOST=0.0.0.0
PORT=8000

echo "📦 Environment: $APP_ENV"
echo "📡 FastAPI Host: $HOST"
echo "🔌 FastAPI Port: $PORT"

# Wait for Postgres
echo "⏳ Waiting for Postgres..."
while ! nc -z db 5432; do
    sleep 1
done
echo "✅ Postgres started"

# Run migrations
echo "🗄️ Running migrations..."
if alembic upgrade head; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

# Start server

if [ "$APP_ENV" = "dev" ]; then
    echo "🔧 Starting in development mode..."
    uvicorn app.main:app --host "$HOST" --port "$PORT" --reload &
else
    echo "🚀 Starting in production mode..."
    uvicorn app.main:app --host "$HOST" --port "$PORT" --workers 2 &
fi

wait -n
