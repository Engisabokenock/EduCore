from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import AppBaseException, app_exception_handler, global_catchall_handler
from app.core.middleware import (
    ContentSanitizationMiddleware,
    ProductionSecurityHeadersMiddleware,
    StructuralAuditLoggerMiddleware,
    TrailingSlashMiddleware,
)
from app.core.cache import redis_pool
from app.core.compress import configure_compression_layers
from app.core.database import engine
from app.api.deps import sliding_window_rate_limiter
from app.api.v1.auth import router as auth_v1_router
from app.api.v1.users import router as users_v1_router
from app.api.v1.cbc import router as cbc_v1_router
from app.api.v1.resources import router as resources_v1_router
from app.api.v1.search import router as search_v1_router
from app.api.v1.downloads import router as downloads_v1_router
from app.api.v1.payments import router as payments_v1_router
from app.api.v1.subscriptions import router as subscriptions_v1_router
from app.api.v1.notifications import router as notifications_v1_router
from app.api.v1.reviews import router as reviews_v1_router
from app.api.v1.analytics import router as analytics_v1_router
from app.api.v1.schools import router as schools_v1_router
from app.api.v1.admin_dashboard import router as admin_control_v1_router

@asynccontextmanager
async def application_lifetime_orchestrator(app: FastAPI):
    """
    Manages global system connectivity mapping states cleanly.

    Ensures persistent database connection pools and Redis clusters boot smoothly,
    and handles graceful teardowns during deployment scale-downs.
    """
    # System Boot Sequence Activity Points
    yield
    # System Teardown / Graceful Shutdown Operations Block
    await engine.dispose()               # Safely drain SQLAlchemy PostgreSQL connection pools
    await redis_pool.disconnect()        # Close Redis socket streams cleanly


# Enforce strict production execution protocols. Drops Swagger Docs when running in Live environments.
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=application_lifetime_orchestrator,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    dependencies=[Depends(sliding_window_rate_limiter)] # Enforce global rate limiting across all routers
)

# -------------------------------------------------------------------------
# CROSS-ORIGIN RESOURCE SHARING (CORS) PRODUCTION GATES
# -------------------------------------------------------------------------
ALLOWED_ORIGINS = ["https://educore.io"]
if settings.FRONTEND_URL:
    ALLOWED_ORIGINS.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False if settings.APP_ENV == "production" else True, # Enforce strict credentials rules on live servers
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Operational Exception Handling Layer bindings
app.add_exception_handler(AppBaseException, app_exception_handler)
app.add_exception_handler(Exception, global_catchall_handler)

# -------------------------------------------------------------------------
# HIGH-SECURITY CUSTOM MIDDLEWARE INJECTIONS
# -------------------------------------------------------------------------
app.add_middleware(TrailingSlashMiddleware)
app.add_middleware(ContentSanitizationMiddleware)
app.add_middleware(ProductionSecurityHeadersMiddleware)
app.add_middleware(StructuralAuditLoggerMiddleware)

# -------------------------------------------------------------------------
# RESPONSE PAYLOAD COMPRESSION PIPELINE
# -------------------------------------------------------------------------
configure_compression_layers(app)

# Version 1 Router Registrations
app.include_router(auth_v1_router, prefix="/api/v1")
app.include_router(users_v1_router, prefix="/api/v1")
app.include_router(cbc_v1_router, prefix="/api/v1")
app.include_router(resources_v1_router, prefix="/api/v1")
app.include_router(search_v1_router, prefix="/api/v1")
app.include_router(downloads_v1_router, prefix="/api/v1")
app.include_router(payments_v1_router, prefix="/api/v1")
app.include_router(subscriptions_v1_router, prefix="/api/v1")
app.include_router(notifications_v1_router, prefix="/api/v1")
app.include_router(reviews_v1_router, prefix="/api/v1")
app.include_router(analytics_v1_router, prefix="/api/v1")
app.include_router(schools_v1_router, prefix="/api/v1")
app.include_router(admin_control_v1_router, prefix="/api/v1")

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Infrastructure Monitoring"])
async def runtime_health_clearance():
    """Validates runtime service availability and reports the active security posture."""
    return {"status": "secured", "environment": settings.APP_ENV, "timestamp": datetime.now(timezone.utc)}
