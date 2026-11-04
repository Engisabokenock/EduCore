"""Subscription lifecycle and premium entitlements (single source of truth)."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.base import User, UserRole
from app.models.payment import PremiumSubscription
from app.models.subscription import SubscriptionPlan, SubscriptionState, UserSubscription

logger = logging.getLogger("educore.subscriptions")

# Roles that always see premium content (staff and educators producing it).
PREMIUM_BYPASS_ROLES = {UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.TEACHER.value}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def subscription_grants_access(sub: Optional[UserSubscription], now: Optional[datetime] = None) -> bool:
    """
    ACTIVE and CANCELED (auto-renew off) keep access until the period ends;
    GRACE_PERIOD keeps access until the grace window closes; EXPIRED never does.
    """
    if sub is None:
        return False
    now = now or _now()
    if sub.status in (SubscriptionState.ACTIVE, SubscriptionState.CANCELED):
        return sub.current_period_end > now
    if sub.status == SubscriptionState.GRACE_PERIOD:
        return bool(sub.grace_period_end and sub.grace_period_end > now)
    return False


async def get_user_subscription(db: AsyncSession, user_id: UUID) -> Optional[UserSubscription]:
    return (await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == user_id)
    )).scalar_one_or_none()


async def has_premium_access(db: AsyncSession, user: Optional[User]) -> bool:
    if user is None:
        return False
    role = user.role.name if user.role else None
    role = role.value if isinstance(role, UserRole) else role
    if role in PREMIUM_BYPASS_ROLES:
        return True
    if subscription_grants_access(await get_user_subscription(db, user.id)):
        return True
    # Legacy premium passes purchased through the original /payments/buy-premium flow.
    legacy = (await db.execute(
        select(PremiumSubscription.id).where(
            PremiumSubscription.user_id == user.id,
            PremiumSubscription.is_active.is_(True),
            PremiumSubscription.expires_at > _now(),
        )
    )).scalar_one_or_none()
    return legacy is not None


async def activate_plan(db: AsyncSession, user_id: UUID, plan: SubscriptionPlan) -> UserSubscription:
    """
    Grant or extend access for a paid plan. Remaining paid time is never lost: a renewal
    stacks on top of the current period end.
    """
    now = _now()
    sub = (await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == user_id).with_for_update(of=UserSubscription)
    )).scalar_one_or_none()
    extension = timedelta(days=plan.duration_days)

    if sub is not None and subscription_grants_access(sub, now):
        sub.current_period_end = max(sub.current_period_end, now) + extension
    else:
        if sub is None:
            sub = UserSubscription(user_id=user_id, plan_id=plan.id, current_period_end=now + extension)
            db.add(sub)
        sub.current_period_start = now
        sub.current_period_end = now + extension

    sub.plan_id = plan.id
    sub.plan = plan
    sub.status = SubscriptionState.ACTIVE
    sub.grace_period_end = None
    sub.auto_renew = True
    await db.flush()
    logger.info("Activated plan %s for user %s until %s", plan.tier, user_id, sub.current_period_end)
    return sub


async def cancel_auto_renew(db: AsyncSession, user_id: UUID) -> Optional[UserSubscription]:
    sub = await get_user_subscription(db, user_id)
    if sub is None or sub.status == SubscriptionState.EXPIRED:
        return None
    sub.auto_renew = False
    if sub.status == SubscriptionState.ACTIVE:
        sub.status = SubscriptionState.CANCELED
    await db.flush()
    return sub


async def expire_now(db: AsyncSession, user_id: UUID) -> None:
    """Immediately revoke access (refunds, administrative termination)."""
    await db.execute(
        update(UserSubscription)
        .where(UserSubscription.user_id == user_id)
        .values(status=SubscriptionState.EXPIRED, auto_renew=False, grace_period_end=None,
                current_period_end=_now())
    )
    await db.execute(
        update(PremiumSubscription).where(PremiumSubscription.user_id == user_id).values(is_active=False)
    )


async def synchronize_lifecycle(db: AsyncSession) -> dict:
    """
    Advance every subscription past its period end. Run on a schedule (cron / worker).

    * CANCELED past period end            -> EXPIRED
    * ACTIVE + auto-renew past period end -> GRACE_PERIOD (time to pay the renewal)
    * ACTIVE without auto-renew past end  -> EXPIRED
    * GRACE_PERIOD past grace end         -> EXPIRED
    """
    now = _now()
    grace_end = now + timedelta(days=settings.SUBSCRIPTION_GRACE_PERIOD_DAYS)

    canceled = await db.execute(
        update(UserSubscription)
        .where(UserSubscription.status == SubscriptionState.CANCELED, UserSubscription.current_period_end <= now)
        .values(status=SubscriptionState.EXPIRED)
    )
    to_grace = await db.execute(
        update(UserSubscription)
        .where(
            UserSubscription.status == SubscriptionState.ACTIVE,
            UserSubscription.current_period_end <= now,
            UserSubscription.auto_renew.is_(True),
        )
        .values(status=SubscriptionState.GRACE_PERIOD, grace_period_end=grace_end)
    )
    lapsed = await db.execute(
        update(UserSubscription)
        .where(
            UserSubscription.status == SubscriptionState.ACTIVE,
            UserSubscription.current_period_end <= now,
            UserSubscription.auto_renew.is_(False),
        )
        .values(status=SubscriptionState.EXPIRED)
    )
    grace_over = await db.execute(
        update(UserSubscription)
        .where(
            UserSubscription.status == SubscriptionState.GRACE_PERIOD,
            or_(UserSubscription.grace_period_end.is_(None), UserSubscription.grace_period_end <= now),
        )
        .values(status=SubscriptionState.EXPIRED, grace_period_end=None)
    )
    result = {
        "canceled_expired": canceled.rowcount or 0,
        "moved_to_grace": to_grace.rowcount or 0,
        "lapsed_expired": lapsed.rowcount or 0,
        "grace_expired": grace_over.rowcount or 0,
    }
    logger.info("Subscription lifecycle sync: %s", result)
    return result
