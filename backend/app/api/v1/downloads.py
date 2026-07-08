import uuid
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_, desc
from typing import Optional
from app.core.database import get_db, AsyncSessionLocal
from app.core.exceptions import AppBaseException, AuthorizationError
from app.api.deps import get_current_user, RoleChecker
from app.models.base import User, UserRole
from app.models.resource import AcademicResource
from app.models.tracking import DownloadLog
from app.schemas.tracking import DownloadLogResponse, DownloadSummaryMetrics

router = APIRouter(prefix="/downloads", tags=["Download Processing Engine"])

# Configuration Limits (Can be bound out to core configurations dynamically)
DAILY_FREE_TIER_LIMIT = 5

async def _persist_download_telemetry(
    resource_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    ip_address: str,
    device_fingerprint: str,
    country_code: str,
) -> None:
    """
    Background worker that de-couples telemetry writes from the critical request path.

    Opens its own session so the HTTP handler can return the CDN URL immediately.
    """
    async with AsyncSessionLocal() as session:
        resource = (
            await session.execute(select(AcademicResource).where(AcademicResource.id == resource_id))
        ).scalar_one_or_none()
        if not resource:
            return
        session.add(
            DownloadLog(
                resource_id=resource.id,
                user_id=user_id,
                ip_address=ip_address,
                device_fingerprint=device_fingerprint[:512],
                country_code=country_code[:3].upper(),
            )
        )
        resource.downloads_count += 1
        session.add(resource)
        await session.commit()

@router.post("/{resource_id}/request", status_code=status.HTTP_200_OK)
async def process_resource_download(
    resource_id: uuid.UUID,
    request: Request,
    user_context: Optional[User] = Depends(get_current_user), # Permissive injection via modified security dependencies
    db: AsyncSession = Depends(get_db)
):
    """Executes structural safety evaluations, premium validations, and downloads enforcement limits."""
    # 1. Verification of Target Asset Lifecycle State
    res_stmt = await db.execute(select(AcademicResource).where(AcademicResource.id == resource_id))
    resource = res_stmt.scalar_one_or_none()
    if not resource or resource.is_archived:
        raise AppBaseException("Target binary asset payload allocation node is missing or archived", 404)

    # 2. Premium Status Authorization Firewall Rule
    if resource.is_premium:
        if not user_context:
            raise AuthorizationError("Premium content items require valid authenticated user sessions")
        if user_context.role.name not in [UserRole.ADMIN, UserRole.TEACHER]:
            # Structural simulation space for subscription vector checks on standard users
            is_premium_subscriber = False
            if not is_premium_subscriber:
                raise AuthorizationError("Active subscription tier missing for required access payload parameters")

    # 3. Dynamic Rate Limiting & Capacity Budget Check
    ip_addr = request.client.host if request.client else "0.0.0.0"
    user_id_val = user_context.id if user_context else None

    # Track usage caps for Free Tier standard account nodes (Admins and Teachers bypass checks)
    if not resource.is_premium and (not user_context or user_context.role.name == UserRole.STUDENT):
        today_floor = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        limit_stmt = select(func.count(DownloadLog.id)).where(
            and_(
                or_(DownloadLog.user_id == user_id_val, DownloadLog.ip_address == ip_addr),
                DownloadLog.downloaded_at >= today_floor
            )
        )
        count_res = await db.execute(limit_stmt)
        if count_res.scalar() >= DAILY_FREE_TIER_LIMIT:
            raise AppBaseException("Daily operational file allocation limits reached for this client instance context", 429)

    # 4. Telemetry Assembly & Parsing Pipeline
    user_agent_string = request.headers.get("user-agent", "Unknown Operational Engine Platform/1.0")
    geo_country_code = request.headers.get("cf-ipcountry", "KE") # Leverages Cloudflare edge geolocation forwarding headers

    download_record = DownloadLog(
        resource_id=resource.id,
        user_id=user_id_val,
        ip_address=ip_addr,
        device_fingerprint=user_agent_string[:512],
        country_code=geo_country_code[:3].upper()
    )
    db.add(download_record)

    # 5. Core Asset Counters Updates
    resource.downloads_count += 1
    db.add(resource)

    await db.flush()
    return {
        "download_clearance_token": secrets.token_urlsafe(32),
        "target_cdn_binary_url": resource.pdf_url
    }

@router.get("/history", response_model=list[DownloadLogResponse])
async def get_user_download_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full interaction chronological logs tracking execution vectors for the authenticated context."""
    stmt = select(DownloadLog).where(
        DownloadLog.user_id == current_user.id
    ).order_by(desc(DownloadLog.downloaded_at)).limit(limit).offset(offset)

    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/metrics/telemetry", response_model=DownloadSummaryMetrics, dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def get_system_wide_telemetry_metrics(db: AsyncSession = Depends(get_db)):
    """Computes real-time aggregation data summaries optimized for management dash monitoring engines."""
    # Compute base volumes parameters
    total_downloads_stmt = select(func.count(DownloadLog.id))
    unique_users_stmt = select(func.count(func.distinct(DownloadLog.user_id)))

    total_res = await db.execute(total_downloads_stmt)
    users_res = await db.execute(unique_users_stmt)

    # Run analytical breakdown matrix maps by geographic criteria
    geo_stmt = select(DownloadLog.country_code, func.count(DownloadLog.id)).group_by(DownloadLog.country_code)
    geo_res = await db.execute(geo_stmt)
    geo_mapping = {row[0]: row[1] for row in geo_res.all()}

    # Extract format performance traces across variations
    variant_stmt = select(AcademicResource.type_variant, func.count(DownloadLog.id)).join(
        DownloadLog, DownloadLog.resource_id == AcademicResource.id
    ).group_by(AcademicResource.type_variant)
    variant_res = await db.execute(variant_stmt)
    variant_mapping = {str(row[0].value): row[1] for row in variant_res.all()}

    return {
        "total_downloads": total_res.scalar() or 0,
        "unique_users_count": users_res.scalar() or 0,
        "downloads_by_country": geo_mapping,
        "downloads_by_type": variant_mapping
    }

@router.post("/{resource_id}/async-process", status_code=status.HTTP_200_OK)
async def register_download_performance_vector(
    resource_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    user_context: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    De-couples telemetry write cycles from critical request/response paths.

    Returns the CDN URL immediately while heavy structural telemetry logging is
    offloaded to a low-overhead background worker.
    """
    resource = (
        await db.execute(select(AcademicResource).where(AcademicResource.id == resource_id))
    ).scalar_one_or_none()
    if not resource or resource.is_archived:
        raise AppBaseException("Target binary asset payload allocation node is missing or archived", 404)

    # Premium status authorization firewall rule (gating still happens on the critical path).
    if resource.is_premium:
        if not user_context:
            raise AuthorizationError("Premium content items require valid authenticated user sessions")
        if user_context.role.name not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise AuthorizationError("Active subscription tier missing for required access payload parameters")

    ip_addr = request.client.host if request.client else "0.0.0.0"
    user_agent_string = request.headers.get("user-agent", "Unknown Operational Engine Platform/1.0")
    geo_country_code = request.headers.get("cf-ipcountry", "KE")

    # Offload telemetry persistence to a background worker so the CDN URL returns without delay.
    background_tasks.add_task(
        _persist_download_telemetry,
        resource.id,
        user_context.id if user_context else None,
        ip_addr,
        user_agent_string,
        geo_country_code,
    )

    return {"target_cdn_binary_payload_url": resource.pdf_url}
