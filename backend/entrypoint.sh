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

# One-time staff bootstrap. Runs inside the deployment, so it always writes to the same
# database the live API uses. Set the variables, redeploy, sign in, then delete them.
if [ -n "$DATABASE_URL" ] && [ -n "$OWNER_BOOTSTRAP_PASSWORD" ]; then
  echo "[startup] Provisioning the platform owner (Super Admin) account..."
  if ! EDUCORE_ACCOUNT_PASSWORD="$OWNER_BOOTSTRAP_PASSWORD" python -m scripts.create_superadmin; then
    echo "[startup] Owner provisioning failed; see the error above"
  fi
  echo "[startup] Remove OWNER_BOOTSTRAP_PASSWORD from the environment once you have signed in."
fi
if [ -n "$DATABASE_URL" ] && [ -n "$ADMIN_BOOTSTRAP_EMAIL" ] && [ -n "$ADMIN_BOOTSTRAP_PASSWORD" ]; then
  echo "[startup] Provisioning administrator $ADMIN_BOOTSTRAP_EMAIL..."
  if ! EDUCORE_ACCOUNT_PASSWORD="$ADMIN_BOOTSTRAP_PASSWORD" python -m scripts.create_staff_account --role admin --email "$ADMIN_BOOTSTRAP_EMAIL"; then
    echo "[startup] Administrator provisioning failed; see the error above"
  fi
  echo "[startup] Remove ADMIN_BOOTSTRAP_EMAIL and ADMIN_BOOTSTRAP_PASSWORD once the admin has signed in."
fi

echo "[startup] Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"   --proxy-headers --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-*}"   --workers "${WEB_CONCURRENCY:-2}"
