import os
import dj_database_url
from .base import *  # noqa: F401, F403

DEBUG = False

# ── Secret key ────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable is required")

# ── Allowed hosts ─────────────────────────────────────────────────────────────
# Accept comma-separated list. Falls back to wildcard so the app can START
# even before the env var is set — tighten in Railway dashboard post-deploy.
_raw_hosts = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(",") if h.strip()] or ["*"]

# ── HTTPS / proxy settings ─────────────────────────────────────────────────────
# Railway terminates TLS at the edge proxy, so we trust the X-Forwarded-Proto
# header. SECURE_SSL_REDIRECT is handled by Railway's edge — disable it here to
# avoid redirect loops behind the proxy.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── CORS ──────────────────────────────────────────────────────────────────────
_raw_cors = os.environ.get("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [o.strip() for o in _raw_cors.split(",") if o.strip()]
if not CORS_ALLOWED_ORIGINS:
    # Allow all in absence of config so Railway health checks work — lock down later
    CORS_ALLOW_ALL_ORIGINS = True

# ── Database — prefer DATABASE_URL (Railway PostgreSQL plugin) ────────────────
_database_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
if _database_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    DATABASES["default"].setdefault("OPTIONS", {})["connect_timeout"] = 10
# else: base.py DATABASES (individual POSTGRES_* vars) remains in effect

# ── Static files — WhiteNoise (no S3 needed for static assets) ────────────────
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": os.environ.get("CLOUD_STORAGE_CONTAINER", "educore-media"),
            "region_name": os.environ.get("CLOUD_STORAGE_REGION", "eu-central-1"),
            "custom_domain": os.environ.get("CLOUD_STORAGE_CUSTOM_DOMAIN", ""),
            "querystring_auth": False,
        },
    },
}

# Fall back to local media storage if S3 is not configured
if not os.environ.get("CLOUD_STORAGE_CONTAINER"):
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    }

# ── Logging — console only (Railway streams stdout/stderr to its log UI) ─────
# File handlers MUST NOT be used: Railway's filesystem is ephemeral and the
# logs/ directory will not exist, causing Django to crash on startup.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "config.logging.JSONFormatter",
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {"handlers": ["console"], "level": "ERROR"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "config": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ── Performance ───────────────────────────────────────────────────────────────
CACHED_LOADER_ENABLED = True

REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}
