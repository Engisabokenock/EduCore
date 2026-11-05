"""Platform-wide activity monitoring. Super Admin only."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker
from app.core.database import get_db
from app.models.activity import ActivityCategory
from app.schemas.approvals import ActivityPage, ActivitySummary
from app.services import activity_service

router = APIRouter(prefix="/security-control-plane/activity", tags=["Activity Monitoring"])

# An empty allow-list admits only the Super Admin (RoleChecker always adds SUPER_ADMIN).
platform_owner = Depends(RoleChecker([]))


@router.get("", response_model=ActivityPage, dependencies=[platform_owner])
async def list_activity(
    category: Optional[ActivityCategory] = Query(None),
    action: Optional[str] = Query(None, max_length=80, description="Action or action prefix, e.g. 'auth.'"),
    actor_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None, min_length=2, max_length=100,
                                  description="Matches the summary, actor e-mail or IP address"),
    since: Optional[datetime] = Query(None),
    until: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    return await activity_service.list_activity(
        db,
        category=category.value if category else None,
        action=action,
        actor_id=actor_id,
        search=search,
        since=since,
        until=until,
        page=page,
        page_size=page_size,
    )


@router.get("/summary", response_model=ActivitySummary, dependencies=[platform_owner])
async def activity_summary(
    hours: int = Query(24, ge=1, le=24 * 90),
    db: AsyncSession = Depends(get_db),
):
    return await activity_service.summary(db, hours=hours)
