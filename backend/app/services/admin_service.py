"""Read models for the admin panel (staff-only listings that public endpoints never expose)."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import raiseload

from app.models.base import Profile, User
from app.models.cbc import Grade, Subject
from app.models.resource import AcademicResource
from app.models.subscription import SubscriptionPlan, SubscriptionState, UserSubscription

RESOURCE_STATUSES = ("all", "published", "draft", "archived")


def _resource_status(resource: AcademicResource) -> str:
    if resource.is_archived:
        return "archived"
    return "published" if resource.is_published else "draft"


async def list_resources(
    db: AsyncSession,
    *,
    status: str = "all",
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    """Every resource, including drafts and archived ones, for staff management."""
    conditions = [true()]
    if status == "published":
        conditions += [AcademicResource.is_published.is_(True), AcademicResource.is_archived.is_(False)]
    elif status == "draft":
        conditions += [AcademicResource.is_published.is_(False), AcademicResource.is_archived.is_(False)]
    elif status == "archived":
        conditions.append(AcademicResource.is_archived.is_(True))
    if search:
        term = search.strip().lower()
        conditions.append(or_(
            func.lower(AcademicResource.title).contains(term, autoescape=True),
            func.lower(AcademicResource.slug).contains(term, autoescape=True),
        ))

    where = and_(*conditions)
    total = (await db.execute(select(func.count(AcademicResource.id)).where(where))).scalar() or 0
    rows = (await db.execute(
        select(AcademicResource, Grade.name, Subject.name)
        .options(raiseload("*"))
        .join(Grade, Grade.id == AcademicResource.grade_id)
        .join(Subject, Subject.id == AcademicResource.subject_id)
        .where(where)
        .order_by(AcademicResource.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).all()
    return {
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "slug": r.slug,
                "type_variant": r.type_variant.value if hasattr(r.type_variant, "value") else str(r.type_variant),
                "grade": grade_name,
                "subject": subject_name,
                "term": int(r.term.value if hasattr(r.term, "value") else r.term),
                "year": r.year,
                "is_premium": r.is_premium,
                "status": _resource_status(r),
                "views_count": r.views_count,
                "downloads_count": r.downloads_count,
                "created_at": r.created_at,
                "published_at": r.published_at,
            }
            for r, grade_name, subject_name in rows
        ],
        "total": int(total),
        "page": page,
        "page_size": page_size,
    }


async def list_subscriptions(
    db: AsyncSession,
    *,
    status: Optional[SubscriptionState] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    conditions = [true()]
    if status is not None:
        conditions.append(UserSubscription.status == status)
    if search:
        term = search.strip().lower()
        conditions.append(or_(
            func.lower(User.email).contains(term, autoescape=True),
            func.lower(func.coalesce(Profile.full_name, "")).contains(term, autoescape=True),
        ))

    base = (
        select(UserSubscription, User.email, Profile.full_name, SubscriptionPlan.name)
        .options(raiseload("*"))
        .join(User, User.id == UserSubscription.user_id)
        .outerjoin(Profile, Profile.user_id == User.id)
        .join(SubscriptionPlan, SubscriptionPlan.id == UserSubscription.plan_id)
        .where(and_(*conditions))
    )
    total = (await db.execute(
        select(func.count()).select_from(base.with_only_columns(UserSubscription.id).subquery())
    )).scalar() or 0
    rows = (await db.execute(
        base.order_by(UserSubscription.current_period_end.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).all()

    now = datetime.now(timezone.utc)
    return {
        "items": [
            {
                "id": sub.id,
                "user_id": sub.user_id,
                "user_email": email,
                "user_name": name,
                "plan_name": plan_name,
                "status": sub.status.value if hasattr(sub.status, "value") else str(sub.status),
                "auto_renew": sub.auto_renew,
                "current_period_start": sub.current_period_start,
                "current_period_end": sub.current_period_end,
                "is_current": sub.current_period_end > now and sub.status != SubscriptionState.EXPIRED,
            }
            for sub, email, name, plan_name in rows
        ],
        "total": int(total),
        "page": page,
        "page_size": page_size,
    }
