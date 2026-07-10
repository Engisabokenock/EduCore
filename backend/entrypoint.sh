#!/bin/sh
set -e

if [ -n "$DATABASE_URL" ]; then
  echo "[startup] Applying database migrations..."
  if ! alembic upgrade head; then
    echo "[startup] Alembic migration failed; starting uvicorn anyway for diagnostics"
  fi
else
  echo "[startup] DATABASE_URL not set; skipping alembic migrations"
fi

echo "[startup] Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
