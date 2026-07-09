import html
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("educore.security.audit")


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """
    Normalizes request paths so trailing-slash URLs (e.g. ``/auth/register/``)
    resolve to their non-slash route definitions (``/auth/register``).

    The Next.js client consistently calls paths with a trailing slash; this keeps
    the backend route definitions clean without per-route slash aliases.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.scope.get("path", "")
        if len(path) > 1 and path.endswith("/"):
            request.scope["path"] = path.rstrip("/")
        return await call_next(request)


class ContentSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Blocks Cross-Site Scripting (XSS) vectors.

    Intercepts and cleanses incoming query strings prior to routing parameter ingestion.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Sanitize query parameters text matrices safely
        if request.query_params:
            sanitized_params = {k: html.escape(v) for k, v in request.query_params.items()}
            request.scope["query_string"] = bytes(
                "&".join(f"{k}={v}" for k, v in sanitized_params.items()), "utf-8"
            )
        return await call_next(request)


class ProductionSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects industry-standard HTTP security headers into every outbound network response."""
    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; object-src 'none';"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"  # Enforce HTTPS Always
        return response


class StructuralAuditLoggerMiddleware(BaseHTTPMiddleware):
    """
    Tracks and records system operations and user actions.

    Logs client execution pathways, target endpoints, response statuses, and identity vectors.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "0.0.0.0"
        method = request.method
        path = request.url.path

        response = await call_next(request)

        logger.info(
            f"AUDIT TRAIL: IP={client_ip} | METHOD={method} | PATH={path} | STATUS={response.status_code}"
        )
        return response
