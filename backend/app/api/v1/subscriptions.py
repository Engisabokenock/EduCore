from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.exceptions import AppBaseException
from app.models.base import User, UserRole
from app.models.subscription import SubscriptionPlan
from app.schemas.payment import StkPushResponse
from app.schemas.subscription import SubscriptionPlanResponse, TriggerSubscriptionRenewal, UserSubscriptionResponse
from app.services import payment_service, subscription_service

router = APIRouter(prefix="/subscriptions", tags=["Subscription Ledger & Billing Lifecycle Engines"])


def _with_access(sub) -> Optional[dict]:
    if sub is None:
        return None
    data = UserSubscriptionResponse.model_validate(sub).model_dump()
    data["has_access"] = subscription_service.subscription_grants_access(sub)
    return data


@router.get("/plans", response_model=list[SubscriptionPlanResponse])
async def fetch_available_monetization_plans(db: AsyncSession = Depends(get_db)):
    """Active plans in display order."""
    stmt = (
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_available.is_(True))
        .order_by(SubscriptionPlan.sort_order, SubscriptionPlan.price)
    )
    return (await db.execute(stmt)).scalars().all()


@router.get("/me", response_model=Optional[UserSubscriptionResponse])
async def query_my_subscription_state(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """The caller's subscription, or null when they have never subscribed."""
    return _with_access(await subscription_service.get_user_subscription(db, current_user.id))


@router.post("/renew", response_model=StkPushResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_contract_renewal(
    payload: TriggerSubscriptionRenewal,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start payment for a plan. Access is granted only when M-Pesa confirms the payment
    (previously this endpoint activated paid plans without any payment).
    """
    transaction = await payment_service.start_checkout(db, current_user, payload.plan_id, payload.phone_number)
    return {
        "success": True,
        "message": "Check your phone and enter your M-Pesa PIN to complete the renewal.",
        "checkout_request_id": transaction.checkout_request_id,
        "merchant_request_id": transaction.merchant_request_id,
        "amount": float(transaction.amount),
    }


@router.post("/cancel", response_model=UserSubscriptionResponse)
async def cancel_subscription_auto_renew(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Turn off auto-renew. Access continues until the end of the paid period."""
    sub = await subscription_service.cancel_auto_renew(db, current_user.id)
    if sub is None:
        raise AppBaseException("You do not have an active subscription to cancel.", 400)
    return _with_access(sub)


@router.post("/engine/synchronize-billing", dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def system_cron_synchronize_billing_cycles(db: AsyncSession = Depends(get_db)):
    """Advance subscriptions past their period end. Call from a scheduler (e.g. hourly)."""
    return {"status": "success", **(await subscription_service.synchronize_lifecycle(db))}
