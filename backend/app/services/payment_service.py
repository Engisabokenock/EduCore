"""M-Pesa checkout, callback settlement and reconciliation."""
import logging
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.exceptions import AppBaseException, AuthorizationError, NotFoundError
from app.core.mpesa import MpesaClient
from app.core.security import constant_time_equals
from app.models.base import User
from app.models.notification import NotificationChannel, NotificationEvent, NotificationLog
from app.models.payment import PaymentTransaction, PremiumSubscription, TransactionStatus
from app.models.subscription import SubscriptionPlan
from app.schemas.payment import MpesaCallbackPayload
from app.models.activity import ActivityCategory
from app.services import activity_service, subscription_service

logger = logging.getLogger("educore.payments")

# Daraja reports "request still being processed" with this error code on STK queries.
_STK_STILL_PROCESSING = "500.001.1001"
_RECONCILE_AFTER = timedelta(seconds=30)
_PENDING_COOLDOWN = timedelta(seconds=20)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def account_reference_for(user: User) -> str:
    return f"EDU{user.id.hex[:8].upper()}"


async def start_checkout(db: AsyncSession, user: User, plan_id: UUID, phone_number: str,
                         mpesa: Optional[MpesaClient] = None) -> PaymentTransaction:
    """Create a pending transaction for ``plan`` and push an STK prompt to the phone."""
    plan = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))).scalar_one_or_none()
    if plan is None or not plan.is_available:
        raise AppBaseException("That plan is not available. Please pick another plan.", 400)

    recent = (await db.execute(
        select(PaymentTransaction.id).where(
            PaymentTransaction.user_id == user.id,
            PaymentTransaction.status == TransactionStatus.PENDING.value,
            PaymentTransaction.created_at > _now() - _PENDING_COOLDOWN,
        ).limit(1)
    )).scalar_one_or_none()
    if recent:
        raise AppBaseException("A payment prompt was just sent to your phone. Complete it or wait a moment.", 429)

    amount = int(math.ceil(Decimal(plan.price)))
    reference = account_reference_for(user)
    gateway = await (mpesa or MpesaClient()).send_stk_push(
        phone_number=phone_number, amount=amount, account_reference=reference,
        description=f"EduCore {plan.tier.value if hasattr(plan.tier, 'value') else plan.tier}",
    )

    transaction = PaymentTransaction(
        user_id=user.id,
        plan_id=plan.id,
        amount=amount,
        phone_number=phone_number,
        account_reference=reference,
        merchant_request_id=gateway["MerchantRequestID"],
        checkout_request_id=gateway["CheckoutRequestID"],
        status=TransactionStatus.PENDING.value,
    )
    db.add(transaction)
    await db.flush()
    activity_service.record(
        db, action="payment.checkout_started", category=ActivityCategory.PAYMENT,
        summary=f"{user.email} started a KES {amount} M-Pesa checkout for {plan.name}", actor=user,
        target_type="payment", target_id=transaction.id,
        details={"plan_id": str(plan.id), "amount": amount, "checkout_request_id": transaction.checkout_request_id},
    )
    logger.info("STK push %s started for user %s plan %s", transaction.checkout_request_id, user.id, plan.tier)
    return transaction


def verify_callback_token(token: Optional[str]) -> None:
    secret = settings.MPESA_CALLBACK_SECRET
    if secret:
        if not token or not constant_time_equals(token, secret):
            raise AuthorizationError("Invalid callback signature.")
        return
    if settings.is_production:
        logger.critical("MPESA_CALLBACK_SECRET is not set; rejecting unauthenticated M-Pesa callback.")
        raise AuthorizationError("Callback authentication is not configured.")
    logger.warning("MPESA_CALLBACK_SECRET not set; accepting unauthenticated callback (non-production only).")


async def _lock_transaction(db: AsyncSession, checkout_request_id: str) -> Optional[PaymentTransaction]:
    return (await db.execute(
        select(PaymentTransaction)
        .where(PaymentTransaction.checkout_request_id == checkout_request_id)
        .with_for_update(of=PaymentTransaction)
    )).scalar_one_or_none()


async def _grant_purchase(db: AsyncSession, transaction: PaymentTransaction) -> None:
    if transaction.plan_id:
        plan = (await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == transaction.plan_id)
        )).scalar_one_or_none()
        if plan is not None:
            await subscription_service.activate_plan(db, transaction.user_id, plan)
            return
    # Legacy transactions (created before plans were attached) buy a 30-day pass.
    legacy = (await db.execute(
        select(PremiumSubscription).where(PremiumSubscription.user_id == transaction.user_id).with_for_update()
    )).scalar_one_or_none()
    now = _now()
    if legacy and legacy.is_active and legacy.expires_at > now:
        legacy.expires_at += timedelta(days=30)
    else:
        if legacy is None:
            legacy = PremiumSubscription(user_id=transaction.user_id, expires_at=now)
            db.add(legacy)
        legacy.expires_at = now + timedelta(days=30)
        legacy.is_active = True


def _notify_success(db: AsyncSession, transaction: PaymentTransaction, recipient: str) -> None:
    db.add(NotificationLog(
        user_id=transaction.user_id,
        event_type=NotificationEvent.PAYMENT_SUCCESS,
        channel=NotificationChannel.PUSH,
        recipient_address=recipient[:255],
        title="Payment received",
        body=f"We received KES {int(transaction.amount)}. Premium access is now active.",
        data={"checkout_request_id": transaction.checkout_request_id,
              "receipt": transaction.mpesa_receipt_number},
        is_sent=True,
    ))


async def _complete(db: AsyncSession, transaction: PaymentTransaction, receipt: Optional[str]) -> None:
    if receipt:
        clash = (await db.execute(
            select(PaymentTransaction.id).where(
                PaymentTransaction.mpesa_receipt_number == receipt,
                PaymentTransaction.id != transaction.id,
            )
        )).scalar_one_or_none()
        if clash:
            logger.error("Receipt %s already settled another transaction; ignoring replay", receipt)
            return
    transaction.mpesa_receipt_number = receipt
    transaction.status = TransactionStatus.COMPLETED.value
    transaction.failure_reason = None
    await _grant_purchase(db, transaction)
    user = (await db.execute(select(User).where(User.id == transaction.user_id))).scalar_one_or_none()
    _notify_success(db, transaction, user.email if user else "unknown")
    activity_service.record(
        db, action="payment.completed", category=ActivityCategory.PAYMENT,
        summary=f"Payment of KES {int(transaction.amount)} completed for {user.email if user else transaction.user_id}",
        actor_id=transaction.user_id, actor_email=user.email if user else None,
        target_type="payment", target_id=transaction.id,
        details={"receipt": receipt, "amount": int(transaction.amount)},
    )
    await db.flush()


async def handle_callback(db: AsyncSession, payload: MpesaCallbackPayload, token: Optional[str]) -> dict:
    """
    Settle an STK push from Daraja's asynchronous callback.

    Safe against forged requests (shared secret), duplicates and replays (row lock and
    PENDING-only transitions) and under-payment (amount verification).
    """
    verify_callback_token(token)
    callback = payload.Body.stkCallback
    transaction = await _lock_transaction(db, callback.CheckoutRequestID)
    if transaction is None:
        logger.error("Callback for unknown CheckoutRequestID %s", callback.CheckoutRequestID)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    items = callback.CallbackMetadata.Item if callback.CallbackMetadata else []
    metadata = {item.Name: item.Value for item in items if item.Value is not None}
    receipt = metadata.get("MpesaReceiptNumber")

    if transaction.status != TransactionStatus.PENDING.value:
        # Already settled (e.g. by status reconciliation). Only backfill a missing receipt.
        if (transaction.status == TransactionStatus.COMPLETED.value and callback.ResultCode == 0
                and receipt and not transaction.mpesa_receipt_number):
            transaction.mpesa_receipt_number = str(receipt)
            transaction.raw_callback_payload = payload.model_dump()
            await db.flush()
        logger.info("Duplicate callback for %s ignored (status=%s)", transaction.checkout_request_id, transaction.status)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    transaction.raw_callback_payload = payload.model_dump()

    if callback.ResultCode != 0:
        transaction.status = TransactionStatus.FAILED.value
        transaction.failure_reason = (callback.ResultDesc or "Payment was not completed")[:255]
        await db.flush()
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    paid = Decimal(str(metadata.get("Amount", "0")))
    if paid < Decimal(transaction.amount):
        transaction.status = TransactionStatus.FAILED.value
        transaction.failure_reason = f"Amount mismatch: paid {paid}, expected {transaction.amount}"
        logger.error("Under-payment on %s: %s", transaction.checkout_request_id, transaction.failure_reason)
        await db.flush()
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    await _complete(db, transaction, str(receipt) if receipt else None)
    logger.info("Payment %s settled with receipt %s", transaction.checkout_request_id, receipt)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


async def get_checkout_status(db: AsyncSession, user: User, checkout_request_id: str,
                              mpesa: Optional[MpesaClient] = None) -> PaymentTransaction:
    """
    Status for the paying user's polling UI. If the callback is late, ask Daraja
    directly so a lost callback never leaves a paying customer without access.
    """
    transaction = await _lock_transaction(db, checkout_request_id)
    if transaction is None or transaction.user_id != user.id:
        raise NotFoundError("Payment not found.")

    if (
        transaction.status == TransactionStatus.PENDING.value
        and settings.mpesa_configured
        and transaction.created_at < _now() - _RECONCILE_AFTER
    ):
        try:
            result = await (mpesa or MpesaClient()).query_stk_status(checkout_request_id)
        except AppBaseException as exc:
            logger.warning("STK status query failed for %s: %s", checkout_request_id, exc.message)
            return transaction
        if result.get("errorCode") == _STK_STILL_PROCESSING:
            return transaction
        result_code = str(result.get("ResultCode", ""))
        if result_code == "0":
            # The query API confirms success but does not return the receipt number;
            # it is filled in if the callback arrives later.
            await _complete(db, transaction, None)
        elif result_code:
            transaction.status = TransactionStatus.FAILED.value
            transaction.failure_reason = (result.get("ResultDesc") or "Payment was not completed")[:255]
            await db.flush()
    return transaction


async def refund(db: AsyncSession, transaction_id: UUID, actor: Optional[User] = None) -> PaymentTransaction:
    transaction = (await db.execute(
        select(PaymentTransaction).where(PaymentTransaction.id == transaction_id).with_for_update(of=PaymentTransaction)
    )).scalar_one_or_none()
    if transaction is None:
        raise NotFoundError("Transaction not found.")
    if transaction.status != TransactionStatus.COMPLETED.value:
        raise AppBaseException("Only completed payments can be refunded.", 400)
    transaction.status = TransactionStatus.REFUNDED.value
    await subscription_service.expire_now(db, transaction.user_id)
    activity_service.record(
        db, action="payment.refunded", category=ActivityCategory.PAYMENT,
        summary=f"Refunded KES {int(transaction.amount)} (receipt {transaction.mpesa_receipt_number or 'n/a'})",
        actor=actor, target_type="payment", target_id=transaction.id,
        details={"user_id": str(transaction.user_id)},
    )
    await db.flush()
    return transaction
