import uuid
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc
from app.core.database import get_db
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

@router.put("/preferences", response_model=list[PreferenceResponse])
async def update_my_notification_preferences(
    payload: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Overwrites user preference flags for communication delivery channels."""
    for preference in payload.preferences:
        stmt = select(NotificationPreference).where(
            and_(
                NotificationPreference.user_id == current_user.id,
                NotificationPreference.event_type == preference.event_type,
                NotificationPreference.channel == preference.channel
            )
        )
        ctx = await db.execute(stmt)
        record = ctx.scalar_one_or_none()

        if not record:
            record = NotificationPreference(
                user_id=current_user.id,
                event_type=preference.event_type,
                channel=preference.channel
            )
        record.is_enabled = preference.is_enabled
        db.add(record)

    await db.flush()

    # Return fresh state representation logs array
    fresh_stmt = select(NotificationPreference).where(NotificationPreference.user_id == current_user.id)
    fresh_ctx = await db.execute(fresh_stmt)
    return fresh_ctx.scalars().all()

@router.get("/history", response_model=list[NotificationLogResponse])
async def get_my_notification_delivery_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Fetches an audit trail ledger of communications dispatched to this user profile container."""
    stmt = select(NotificationLog).where(
        NotificationLog.user_id == current_user.id
    ).order_by(desc(NotificationLog.sent_at)).limit(limit).offset(offset)

    res = await db.execute(stmt)
    return res.scalars().all()
