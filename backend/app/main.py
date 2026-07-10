from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, status, Depends
from fastapi.middleware.cors import CORSMiddleware

# Core configurations and security guards
from app.core.config import settings
from app.core.exceptions import AppBaseException, app_exception_handler, global_catchall_handler
from app.core.database import engine
from app.core.cache import redis_pool
from app.core.middleware import (
    ContentSanitizationMiddleware,
    ProductionSecurityHeadersMiddleware,
    StructuralAuditLoggerMiddleware,
    TrailingSlashMiddleware,
)
from app.core.compress import configure_compression_layers
from app.core.lifespan import startup_create_tables
from app.api.deps import sliding_window_rate_limiter

# -------------------------------------------------------------------------
# IMPORT ALL MODULE ROUTERS (Connecting them to the system)
# -------------------------------------------------------------------------
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.cbc import router as cbc_router
from app.api.v1.resources import router as content_router
from app.api.v1.search import router as search_router
from app.api.v1.downloads import router as downloads_router
from app.api.v1.payments import router as payments_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.schools import router as schools_router
from app.api.v1.admin_dashboard import router as admin_router, security_router as security_router
from app.api.v1.portal_resources import router as portal_assets_router
from app.api.v1.internal_control_plane import router as internal_control_plane_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles low-overhead pooling connect and teardown loops cleanly."""
    await startup_create_tables()
    yield
    await engine.dispose()
    await redis_pool.disconnect()


# Initialize the global application gateway
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=True,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    dependencies=[Depends(sliding_window_rate_limiter)],
)

# -------------------------------------------------------------------------
# PRODUCTION CROSS-ORIGIN ISOLATION GATES (CORS)
# -------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Attach Security Middlewares
app.add_middleware(TrailingSlashMiddleware)
app.add_middleware(ContentSanitizationMiddleware)
app.add_middleware(ProductionSecurityHeadersMiddleware)
app.add_middleware(StructuralAuditLoggerMiddleware)

# Response Payload Compression Pipeline
configure_compression_layers(app)

# Bind Operational Exception Handlers globally
app.add_exception_handler(AppBaseException, app_exception_handler)
app.add_exception_handler(Exception, global_catchall_handler)

# -------------------------------------------------------------------------
# MOUNT ROUTERS WITH THE EXACT API PREFIX EXPECTED BY THE FRONTEND
# -------------------------------------------------------------------------
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(cbc_router, prefix="/api/v1")
app.include_router(content_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(downloads_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(schools_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(portal_assets_router, prefix="/api/v1")
app.include_router(internal_control_plane_router, prefix="/api/v1")


@app.get("/api/v1/health", status_code=status.HTTP_200_OK, tags=["Infrastructure Monitoring"])
async def root_health_ping():
    """Confirms backend is alive and connected."""
    return {
        "status": "connected",
        "platform": "EduCore Kenya",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
