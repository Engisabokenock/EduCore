"""Download authorization, free-tier quotas and telemetry."""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.exceptions import AppBaseException, AuthenticationError, AuthorizationError, NotFoundError
from app.core.network import get_client_ip, get_country_code, get_user_agent
from app.core.security import safe_filename
from app.models.base import User
from app.models.resource import AcademicResource
from app.models.tracking import DownloadLog
from app.services import subscription_service
from app.storage.r2 import StorageProvider

logger = logging.getLogger("educore.downloads")


async def get_downloadable_resource(db: AsyncSession, *, slug: Optional[str] = None,
                                    resource_id=None) -> AcademicResource:
    stmt = select(AcademicResource)
    stmt = stmt.where(AcademicResource.slug == slug) if slug else stmt.where(AcademicResource.id == resource_id)
    resource = (await db.execute(stmt)).scalar_one_or_none()
    if resource is None or resource.is_archived or not resource.is_published:
        raise NotFoundError("This resource is not available.")
    return resource


async def downloads_today(db: AsyncSession, user: Optional[User], ip: str) -> int:
    midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    # Signed-in users are counted per account; anonymous visitors per IP. (The previous
    # query OR-ed `user_id IS NULL`, which counted every anonymous download site-wide.)
    owner = DownloadLog.user_id == user.id if user else (
        (DownloadLog.user_id.is_(None)) & (DownloadLog.ip_address == ip)
    )
    return (await db.execute(
        select(func.count(DownloadLog.id)).where(owner, DownloadLog.downloaded_at >= midnight)
    )).scalar() or 0


async def can_access(db: AsyncSession, resource: AcademicResource, user: Optional[User]) -> bool:
    if not resource.is_premium:
        return True
    return await subscription_service.has_premium_access(db, user)


async def authorize_and_record(db: AsyncSession, resource: AcademicResource, user: Optional[User],
                               request: Request) -> dict:
    """Enforce entitlement and quota, log the download and return a fetchable URL."""
    ip = get_client_ip(request)
    premium_user = await subscription_service.has_premium_access(db, user)

    if resource.is_premium and not premium_user:
        if user is None:
            raise AuthenticationError("Log in with a premium account to download this resource.")
        raise AuthorizationError("This resource needs an active premium subscription.")

    if not premium_user:
        used = await downloads_today(db, user, ip)
        if used >= settings.DAILY_FREE_DOWNLOAD_LIMIT:
            raise AppBaseException(
                f"You have reached today's limit of {settings.DAILY_FREE_DOWNLOAD_LIMIT} free downloads. "
                "Upgrade to premium for unlimited downloads.", 429,
            )

    db.add(DownloadLog(
        resource_id=resource.id,
        user_id=user.id if user else None,
        ip_address=ip,
        device_fingerprint=get_user_agent(request, 512),
        country_code=get_country_code(request),
    ))
    # Atomic increment: `resource.downloads_count += 1` loses updates under concurrency.
    await db.execute(
        update(AcademicResource)
        .where(AcademicResource.id == resource.id)
        .values(downloads_count=AcademicResource.downloads_count + 1)
    )
    await db.flush()

    url = await StorageProvider().download_url(resource.pdf_url, filename=f"{safe_filename(resource.slug)}.pdf")
    return {"url": url, "expires_in": settings.PRESIGNED_URL_TTL_SECONDS}
