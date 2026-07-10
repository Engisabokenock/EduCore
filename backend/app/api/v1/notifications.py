import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func
from app.core.database import get_db
from app.core.exceptions import AppBaseException
from app.api.deps import get_current_user
from app.models.base import User
from app.models.notification import NotificationPreference, NotificationLog
from app.schemas.notification import UpdatePreferencesRequest, PreferenceResponse, NotificationLogResponse

router = APIRouter(prefix="/notifications", tags=["Notification Ledger & Preference Matrices"])

@router.get("/preferences", response_model=list[PreferenceResponse])
async def fetch_my_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full configuration rules mapped to the current authenticated profile context identity."""
    stmt = select(NotificationPreference).where(NotificationPreference.user_id == current_user.id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("", response_model=list[NotificationLogResponse])
async def list_my_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List notifications for the authenticated user."""
    stmt = select(NotificationLog).where(
        NotificationLog.user_id == current_user.id
    ).order_by(desc(NotificationLog.sent_at)).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    count = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            and_(
                NotificationLog.user_id == current_user.id,
                NotificationLog.is_read == False,
            )
        )
    )).scalar() or 0
    return {"unread_count": count}


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NotificationLog).where(
        and_(
            NotificationLog.id == notification_id,
            NotificationLog.user_id == current_user.id,
        )
    )
    notification = (await db.execute(stmt)).scalar_one_or_none()
    if not notification:
        raise AppBaseException("Notification not found", 404)
    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    db.add(notification)
    await db.flush()


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NotificationLog).where(
        and_(
            NotificationLog.user_id == current_user.id,
            NotificationLog.is_read == False,
        )
    )
    notifications = (await db.execute(stmt)).scalars().all()
    now = datetime.now(timezone.utc)
    for notification in notifications:
        notification.is_read = True
        notification.read_at = now
        db.add(notification)
    await db.flush()

