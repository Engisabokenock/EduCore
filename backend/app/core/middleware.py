import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.network import get_client_ip

logger = logging.getLogger("educore.security.audit")

# Swagger / ReDoc load their assets from a CDN and need inline scripts.
_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")
_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
_DOCS_CSP = (
    "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "img-src 'self' data: https://fastapi.tiangolo.com; font-src 'self' https://fonts.gstatic.com; "
    "frame-ancestors 'none'"
)


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """
    Normalizes request paths so trailing-slash URLs (e.g. ``/auth/register/``)
    resolve to their non-slash route definitions (``/auth/register``).

    The Next.js client consistently calls paths with a trailing slash; this keeps
    the backend route definitions clean without per-route slash aliases or 307
    redirects (which drop POST bodies in some clients).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.scope.get("path", "")
        if len(path) > 1 and path.endswith("/"):
            request.scope["path"] = path.rstrip("/")
        return await call_next(request)


class ProductionSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects standard HTTP security headers into every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        is_docs = request.url.path.startswith(_DOCS_PATHS)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = _DOCS_CSP if is_docs else _API_CSP
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response


class StructuralAuditLoggerMiddleware(BaseHTTPMiddleware):
    """
    Structured access log with a per-request correlation id.

    The id is taken from an inbound ``X-Request-ID`` (set by nginx / the load balancer)
    or generated, echoed back in the response, and included in every log line so a
    user-reported error can be traced end to end.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_id=%s ip=%s method=%s path=%s status=%s duration_ms=%.1f",
            request_id, get_client_ip(request), request.method, request.url.path,
            response.status_code, duration_ms,
        )
        return response
