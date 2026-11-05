import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.network import get_client_ip, get_user_agent
from app.core.request_context import RequestContext, reset_request_context, set_request_context

logger = logging.getLogger("educore.security.audit")

# Swagger / ReDoc load their assets from a CDN and need inline scripts.
_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")
_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"

# State-changing calls are written to the activity log unless a service already recorded
# a richer domain event for the request. Token refreshes are routine and skipped.
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_ACTIVITY_SKIP_PATHS = ("/api/v1/auth/refresh", "/api/v1/auth/token/refresh", "/api/v1/health")
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
        request_id = (request.headers.get("x-request-id") or uuid.uuid4().hex)[:64]
        request.state.request_id = request_id
        ip = get_client_ip(request)
        path = request.url.path.rstrip("/") or "/"
        ctx = RequestContext(
            request_id=request_id, ip_address=ip, user_agent=get_user_agent(request),
            method=request.method, path=path,
        )
        token = set_request_context(ctx)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            reset_request_context(token)
        duration_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_id=%s ip=%s method=%s path=%s status=%s duration_ms=%.1f",
            request_id, ip, request.method, path, response.status_code, duration_ms,
        )
        if (
            request.method in _MUTATING_METHODS
            and path.startswith("/api/")
            and not path.startswith(_ACTIVITY_SKIP_PATHS)
            and not ctx.activity_recorded
        ):
            await self._record_request(request, ctx, response.status_code, duration_ms)
        return response

    @staticmethod
    async def _record_request(request: Request, ctx: RequestContext, status_code: int, duration_ms: float) -> None:
        # Imported lazily: the middleware module is loaded before the ORM is configured.
        from app.core.security import verify_jwt_token
        from app.models.activity import ActivityCategory
        from app.services.activity_service import build_entry, record_entry_detached

        actor_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            try:
                actor_id = uuid.UUID(verify_jwt_token(auth_header[7:].strip(), is_refresh=False)["sub"])
            except Exception:
                actor_id = None

        token = set_request_context(ctx)
        try:
            entry = build_entry(
                action=f"request.{request.method.lower()}",
                category=ActivityCategory.REQUEST,
                summary=f"{request.method} {ctx.path} -> {status_code}",
                actor_id=actor_id,
                status_code=status_code,
                details={"duration_ms": round(duration_ms, 1)},
            )
        finally:
            reset_request_context(token)
        await record_entry_detached(entry)
