#!/usr/bin/env bash
set -euo pipefail

APP_ENV=${APP_ENV:-prod}
HOST=0.0.0.0
PORT=8000

echo "📦 Environment: $APP_ENV"
echo "📡 FastAPI Host: $HOST"
echo "🔌 FastAPI Port: $PORT"

if [ "$APP_ENV" = "dev" ]; then
    echo "🔧 Starting in development mode..."
    uvicorn app.main:app --host "$HOST" --port "$PORT" --reload &
else
    echo "🚀 Starting in production mode..."
    uvicorn app.main:app --host "$HOST" --port "$PORT" --workers 2 &
fi

wait -n
