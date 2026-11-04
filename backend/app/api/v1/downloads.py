import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import RoleChecker, get_current_user, get_optional_user
from app.core.database import get_db
from app.models.base import User, UserRole
from app.models.resource import AcademicResource
from app.models.tracking import DownloadLog
from app.schemas.tracking import DownloadLogResponse, DownloadSummaryMetrics
from app.services import download_service

router = APIRouter(prefix="/downloads", tags=["Download Processing Engine"])


@router.post("/{resource_id}/request", status_code=status.HTTP_200_OK)
async def process_resource_download(
    resource_id: uuid.UUID,
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Entitlement-checked download by resource id (same rules as /resources/{slug}/download)."""
    resource = await download_service.get_downloadable_resource(db, resource_id=resource_id)
    result = await download_service.authorize_and_record(db, resource, user, request)
    # Keep the legacy response key for existing clients.
    return {**result, "target_cdn_binary_url": result["url"]}


@router.get("/history", response_model=list[DownloadLogResponse])
async def get_user_download_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """The authenticated user's download history, newest first."""
    if page:
        offset = (page - 1) * limit
    stmt = (
        select(DownloadLog)
        .where(DownloadLog.user_id == current_user.id)
        .order_by(desc(DownloadLog.downloaded_at))
        .limit(limit)
        .offset(offset)
    )
    return (await db.execute(stmt)).scalars().all()


@router.get("/metrics/telemetry", response_model=DownloadSummaryMetrics, dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def get_system_wide_telemetry_metrics(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(DownloadLog.id)))).scalar() or 0
    unique_users = (await db.execute(select(func.count(func.distinct(DownloadLog.user_id))))).scalar() or 0
    geo = await db.execute(select(DownloadLog.country_code, func.count(DownloadLog.id)).group_by(DownloadLog.country_code))
    variants = await db.execute(
        select(AcademicResource.type_variant, func.count(DownloadLog.id))
        .join(DownloadLog, DownloadLog.resource_id == AcademicResource.id)
        .group_by(AcademicResource.type_variant)
    )
    return {
        "total_downloads": total,
        "unique_users_count": unique_users,
        "downloads_by_country": {row[0]: row[1] for row in geo.all()},
        "downloads_by_type": {row[0].value: row[1] for row in variants.all()},
    }
