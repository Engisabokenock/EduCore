#!/bin/sh
set -e

# Resolve port: Railway provides $PORT; fallback to 8000
PORT="${PORT:-8000}"

echo "Starting Django+Gunicorn on 0.0.0.0:${PORT}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers 3 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
