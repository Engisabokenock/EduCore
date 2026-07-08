#!/bin/sh
set -e

echo "[startup] Applying database migrations..."
alembic upgrade head

echo "[startup] Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
