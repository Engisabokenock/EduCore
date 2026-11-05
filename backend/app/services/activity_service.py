"""
Platform activity log.

Two ways to write:

* ``record`` adds the entry to the caller's database session, so it commits or rolls
  back together with the action it describes (an approval that fails leaves no trace
  claiming it succeeded).
* ``record_detached`` writes in its own short transaction. Use it for events that must
  survive the request failing, such as a rejected login.

Only the Super Admin can read the log (see ``app/api/v1/activity.py``).
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_context import get_request_context
from app.models.activity import ActivityCategory, ActivityLog
from app.models.base import AccountApprovalStatus, Profile, User

logger = logging.getLogger("educore.activity")

_SENSITIVE_KEYS = {"password", "new_password", "old_password", "token", "refresh", "access", "secret"}


def _role_of(user: Optional[User]) -> Optional[str]:
    role = getattr(user, "role", None) if user is not None else None
    if role is None:
        return None
    name = role.name
    return str(name.value if hasattr(name, "value") else name)


def _clean(details: Optional[dict]) -> dict:
    """Drop anything credential-like before it is persisted."""
    if not details:
        return {}
    return {k: v for k, v in details.items() if k.lower() not in _SENSITIVE_KEYS}


def build_entry(
    *,
    action: str,
    category: ActivityCategory | str,
    summary: str,
    actor: Optional[User] = None,
    actor_id: Optional[UUID] = None,
    actor_email: Optional[str] = None,
    actor_role: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Any = None,
    details: Optional[dict] = None,
    status_code: Optional[int] = None,
) -> ActivityLog:
    ctx = get_request_context()
    path = (ctx.path or "")[:255] or None if ctx else None
    return ActivityLog(
        occurred_at=datetime.now(timezone.utc),
        actor_id=actor.id if actor is not None else actor_id,
        actor_email=actor.email if actor is not None else actor_email,
        actor_role=_role_of(actor) or actor_role,
        category=category.value if isinstance(category, ActivityCategory) else str(category),
        action=action[:80],
        summary=summary[:500],
        target_type=target_type,
        target_id=str(target_id)[:64] if target_id is not None else None,
        details=_clean(details),
        ip_address=ctx.ip_address if ctx else None,
        user_agent=ctx.user_agent if ctx else None,
        request_id=ctx.request_id if ctx else None,
        http_method=ctx.method if ctx else None,
        path=path,
        status_code=status_code,
    )


def _mark_recorded() -> None:
    ctx = get_request_context()
    if ctx is not None:
        ctx.activity_recorded = True


def record(db: AsyncSession, **kwargs) -> ActivityLog:
    """Add an activity entry to the current transaction."""
    entry = build_entry(**kwargs)
    db.add(entry)
    _mark_recorded()
    return entry


async def record_detached(**kwargs) -> None:
    """Persist an activity entry in its own transaction. Never raises."""
    _mark_recorded()
    await record_entry_detached(build_entry(**kwargs))


async def record_entry_detached(entry: ActivityLog) -> None:
    """Persist a pre-built entry in its own transaction. Never raises."""
    from app.core.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            session.add(entry)
            await session.commit()
    except Exception:  # the audit trail must never break the request it describes
        logger.exception("Could not persist activity entry %s", entry.action)


# ── Reading ──────────────────────────────────────────────────────────────────

def serialize(entry: ActivityLog, actor_email: Optional[str] = None, actor_name: Optional[str] = None) -> dict:
    return {
        "id": entry.id,
        "occurred_at": entry.occurred_at,
        "actor_id": entry.actor_id,
        "actor_email": entry.actor_email or actor_email,
        "actor_name": actor_name,
        "actor_role": entry.actor_role,
        "category": entry.category,
        "action": entry.action,
        "summary": entry.summary,
        "target_type": entry.target_type,
        "target_id": entry.target_id,
        "details": entry.details or {},
        "ip_address": entry.ip_address,
        "user_agent": entry.user_agent,
        "request_id": entry.request_id,
        "http_method": entry.http_method,
        "path": entry.path,
        "status_code": entry.status_code,
    }


async def list_activity(
    db: AsyncSession,
    *,
    category: Optional[str] = None,
    action: Optional[str] = None,
    actor_id: Optional[UUID] = None,
    search: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    conditions = [true()]
    if category:
        conditions.append(ActivityLog.category == category)
    if action:
        conditions.append(ActivityLog.action.startswith(action, autoescape=True))
    if actor_id:
        conditions.append(ActivityLog.actor_id == actor_id)
    if since:
        conditions.append(ActivityLog.occurred_at >= since)
    if until:
        conditions.append(ActivityLog.occurred_at <= until)
    if search:
        term = search.strip().lower()
        conditions.append(or_(
            func.lower(ActivityLog.summary).contains(term, autoescape=True),
            func.lower(func.coalesce(ActivityLog.actor_email, User.email, "")).contains(term, autoescape=True),
            func.lower(func.coalesce(ActivityLog.ip_address, "")).contains(term, autoescape=True),
        ))

    joined = (
        select(ActivityLog, User.email, Profile.full_name)
        .outerjoin(User, User.id == ActivityLog.actor_id)
        .outerjoin(Profile, Profile.user_id == ActivityLog.actor_id)
        .where(and_(*conditions))
    )
    total = (await db.execute(
        select(func.count()).select_from(joined.with_only_columns(ActivityLog.id).subquery())
    )).scalar() or 0
    rows = (await db.execute(
        joined.order_by(ActivityLog.occurred_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).all()
    return {
        "items": [serialize(entry, email, name) for entry, email, name in rows],
        "total": int(total),
        "page": page,
        "page_size": page_size,
    }


async def summary(db: AsyncSession, hours: int = 24) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    by_category = {
        category: int(count)
        for category, count in (await db.execute(
            select(ActivityLog.category, func.count(ActivityLog.id))
            .where(ActivityLog.occurred_at >= since)
            .group_by(ActivityLog.category)
        )).all()
    }
    failed_logins = (await db.execute(
        select(func.count(ActivityLog.id)).where(
            ActivityLog.occurred_at >= since, ActivityLog.action == "auth.login_failed"
        )
    )).scalar() or 0
    active_users = (await db.execute(
        select(func.count(func.distinct(ActivityLog.actor_id))).where(
            ActivityLog.occurred_at >= since, ActivityLog.actor_id.is_not(None)
        )
    )).scalar() or 0
    pending = (await db.execute(
        select(func.count(User.id)).where(User.approval_status == AccountApprovalStatus.PENDING)
    )).scalar() or 0
    return {
        "window_hours": hours,
        "total_events": sum(by_category.values()),
        "by_category": by_category,
        "failed_logins": int(failed_logins),
        "active_users": int(active_users),
        "pending_approvals": int(pending),
    }
