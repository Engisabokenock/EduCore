import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from app.core.database import get_db
from app.core.exceptions import AppBaseException, AuthorizationError
from app.api.deps import get_current_user, RoleChecker
from app.models.base import User, UserRole
from app.models.subscription import UserSubscription, SubscriptionPlan, SubscriptionState, PlanTier
from app.schemas.subscription import UserSubscriptionResponse, SubscriptionPlanResponse, TriggerSubscriptionRenewal

router = APIRouter(prefix="/subscriptions", tags=["Subscription Ledger & Billing Lifecycle Engines"])

# --- CORE CATALOG MANAGEMENT ---
@router.get("/plans", response_model=list[SubscriptionPlanResponse], status_code=status.HTTP_200_OK)
async def fetch_available_monetization_plans(db: AsyncSession = Depends(get_db)):
    """Retrieves all active platform subscription tiers sorted linearly by price index values."""
    stmt = select(SubscriptionPlan).where(SubscriptionPlan.is_available == True).order_by(SubscriptionPlan.price)
    execution_context = await db.execute(stmt)
    return execution_context.scalars().all()

# --- CLIENT CONTRACT ACCESSIBILITIES ---
@router.get("/me", response_model=UserSubscriptionResponse, status_code=status.HTTP_200_OK)
async def query_my_subscription_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns subscription mapping status vectors tracking the authenticated identity profile context."""
    stmt = select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    execution_context = await db.execute(stmt)
    subscription = execution_context.scalar_one_or_none()

    if not subscription:
        raise AppBaseException("No database contract record tracking found for this specific profile root", 404)
    return subscription

@router.post("/renew", response_model=UserSubscriptionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_contract_renewal(
    payload: TriggerSubscriptionRenewal,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes contract changes to extend structural timelines or switch plans.

    This interface connects to the Phase 7 Safaricom M-Pesa client engine.
    """
    plan_stmt = select(SubscriptionPlan).where(SubscriptionPlan.id == payload.plan_id)
    plan_context = await db.execute(plan_stmt)
    plan = plan_context.scalar_one_or_none()

    if not plan or not plan.is_available:
        raise AppBaseException("The targeted selection code matches an obsolete or missing payment plan configuration node", 400)

    sub_stmt = select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    sub_context = await db.execute(sub_stmt)
    subscription = sub_context.scalar_one_or_none()

    now_utc = datetime.now(timezone.utc)
    time_extension = timedelta(days=plan.duration_days)

    if subscription and subscription.status in [SubscriptionState.ACTIVE, SubscriptionState.GRACE_PERIOD]:
        # Smooth timeline aggregation rollover implementation logic
        subscription.plan_id = plan.id
        subscription.current_period_end = max(subscription.current_period_end, now_utc) + time_extension
        subscription.status = SubscriptionState.ACTIVE
        subscription.grace_period_end = None
    else:
        # Complete fallback allocation block initialization logic
        if not subscription:
            subscription = UserSubscription(user_id=current_user.id)
        subscription.plan_id = plan.id
        subscription.current_period_start = now_utc
        subscription.current_period_end = now_utc + time_extension
        subscription.status = SubscriptionState.ACTIVE
        subscription.grace_period_end = None

    subscription.auto_renew = True
    db.add(subscription)
    await db.flush()
    return subscription

@router.post("/cancel", response_model=UserSubscriptionResponse, status_code=status.HTTP_200_OK)
async def cancel_subscription_auto_renew(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disables automated recurring billing parameters while keeping active assets available until the end of the current cycle."""
    stmt = select(UserSubscription).where(UserSubscription.user_id == current_user.id)
    execution_context = await db.execute(stmt)
    subscription = execution_context.scalar_one_or_none()

    if not subscription or subscription.status == SubscriptionState.EXPIRED:
        raise AppBaseException("No actionable subscription layer context available for cancellation parameters", 400)

    subscription.auto_renew = False
    subscription.status = SubscriptionState.CANCELED
    db.add(subscription)
    await db.flush()
    return subscription

# --- SYSTEM AUTOMATED LIFECYCLE BACKGROUND CRONS ---
@router.post("/engine/synchronize-billing", status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def system_cron_synchronize_billing_cycles(db: AsyncSession = Depends(get_db)):
    """
    Automated Background Daemon Route.

    Scans past-due cycles, handles grace periods, retry loops, and expires accounts.
    """
    now_utc = datetime.now(timezone.utc)
    DEFAULT_SYSTEM_GRACE_PERIOD_DAYS = 3

    # Pipeline A: Transition expired, non-recurring contracts (CANCELED) directly to EXPIRED state
    canceled_expiry_stmt = select(UserSubscription).where(
        and_(
            UserSubscription.status == SubscriptionState.CANCELED,
            UserSubscription.current_period_end <= now_utc
        )
    )
    canceled_expired_records = await db.execute(canceled_expiry_stmt)
    for sub in canceled_expired_records.scalars().all():
        sub.status = SubscriptionState.EXPIRED
        db.add(sub)

    # Pipeline B: Transition expired ACTIVE accounts with auto_renew enabled into a GRACE_PERIOD state
    grace_transition_stmt = select(UserSubscription).where(
        and_(
            UserSubscription.status == SubscriptionState.ACTIVE,
            UserSubscription.current_period_end <= now_utc,
            UserSubscription.auto_renew == True
        )
    )
    grace_transition_records = await db.execute(grace_transition_stmt)
    for sub in grace_transition_records.scalars().all():
        sub.status = SubscriptionState.GRACE_PERIOD
        sub.grace_period_end = now_utc + timedelta(days=DEFAULT_SYSTEM_GRACE_PERIOD_DAYS)
        # Dispatch micro-transaction retry requests down to Phase 7 M-Pesa channels here
        db.add(sub)

    # Pipeline C: Terminate accounts that remain unpaid at the end of their Grace Period
    grace_expiry_stmt = select(UserSubscription).where(
        and_(
            UserSubscription.status == SubscriptionState.GRACE_PERIOD,
            UserSubscription.grace_period_end <= now_utc
        )
    )
    grace_expired_records = await db.execute(grace_expiry_stmt)
    for sub in grace_expired_records.scalars().all():
        sub.status = SubscriptionState.EXPIRED
        sub.grace_period_end = None
        db.add(sub)

    await db.flush()
    return {"status": "success", "message": "Global structural account timeline states synchronized successfully"}
