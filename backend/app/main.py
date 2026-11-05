import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import models as _orm_models  # noqa: F401  (register every ORM mapper before the first request)
from app.api.deps import sliding_window_rate_limiter
from app.core.cache import close_redis, get_redis_client
from app.core.compress import configure_compression_layers
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import (
    AppBaseException,
    app_exception_handler,
    global_catchall_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.middleware import (
    ProductionSecurityHeadersMiddleware,
    StructuralAuditLoggerMiddleware,
    TrailingSlashMiddleware,
)

from app.api.v1.activity import router as activity_router
from app.api.v1.admin_dashboard import router as admin_router, security_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.cbc import router as cbc_router
from app.api.v1.downloads import router as downloads_router
from app.api.v1.internal_control_plane import router as internal_control_plane_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.payments import router as payments_router
from app.api.v1.portal_resources import router as portal_assets_router
from app.api.v1.resources import router as content_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.schools import router as schools_router
from app.api.v1.search import router as search_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.users import router as users_router

logger = logging.getLogger("educore")
API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("EduCore API starting (env=%s)", settings.APP_ENV)
    yield
    await engine.dispose()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.1.0",
    lifespan=lifespan,
    redirect_slashes=False,  # TrailingSlashMiddleware normalises paths without 307 redirects
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
    dependencies=[Depends(sliding_window_rate_limiter)],
)

# Middleware order: the last one added runs first on the request.
configure_compression_layers(app)
app.add_middleware(ProductionSecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,   # never "*" together with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)
app.add_middleware(TrailingSlashMiddleware)
app.add_middleware(StructuralAuditLoggerMiddleware)

app.add_exception_handler(AppBaseException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_catchall_handler)

for router in (
    auth_router, users_router, cbc_router, content_router, search_router, downloads_router,
    payments_router, subscriptions_router, notifications_router, reviews_router,
    analytics_router, schools_router, admin_router, security_router, portal_assets_router,
    internal_control_plane_router, approvals_router, activity_router,
):
    app.include_router(router, prefix=API_PREFIX)


@app.get(f"{API_PREFIX}/health", tags=["Infrastructure Monitoring"])
async def root_health_ping():
    """Liveness and dependency status for load balancers and uptime monitors."""
    checks = {"database": "ok", "redis": "disabled"}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Health check: database unavailable: %s", exc)
        checks["database"] = "unavailable"

    client = get_redis_client()
    if client is not None:
        try:
            async with client:
                await client.ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "unavailable"

    healthy = checks["database"] == "ok"
    return JSONResponse(
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "connected" if healthy else "degraded",
            "platform": "EduCore Kenya",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
