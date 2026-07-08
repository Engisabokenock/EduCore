import uuid
from datetime import datetime, timedelta, timezone
import logging
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.exceptions import AppBaseException
from app.core.mpesa import MpesaClient
from app.api.deps import get_current_user, RoleChecker
from app.models.base import User, UserRole
from app.models.payment import PaymentTransaction, PremiumSubscription, TransactionStatus
from app.schemas.payment import InitiateStkPushRequest, StkPushResponse, TransactionOut, MpesaCallbackPayload

router = APIRouter(prefix="/payments", tags=["M-Pesa Transaction Lifecycle Ledger Core Ecosystem"])
logger = logging.getLogger("educore.callbacks")

@router.post("/buy-premium", response_model=StkPushResponse, status_code=status.HTTP_202_ACCEPTED)
async def initiate_premium_purchase(
    payload: InitiateStkPushRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    mpesa: MpesaClient = Depends()
):
    """
    Step 1 & 2 Flow: Creates local tracking parameters ledger log,
    then requests immediate STK push interface on customer device.
    """
    account_reference = f"EDU-{current_user.id.hex[:8].upper()}"

    # Trigger interaction down to Safaricom network pipelines
    gateway_response = await mpesa.send_stk_push(
        phone_number=payload.phone_number,
        amount=int(payload.amount),
        account_reference=account_reference
    )

    # Guard against atypical API structural response anomalies
    if gateway_response.get("ResponseCode") != "0":
        raise AppBaseException("Safaricom system framework interfaces declined request ingestion paths", 400)

    # Persist pending structural state context mapping logs
    transaction = PaymentTransaction(
        user_id=current_user.id,
        amount=payload.amount,
        phone_number=payload.phone_number,
        merchant_request_id=gateway_response["MerchantRequestID"],
        checkout_request_id=gateway_response["CheckoutRequestID"],
        status=TransactionStatus.PENDING
    )
    db.add(transaction)
    await db.flush()

    return {
        "success": True,
        "message": "STK Push dispatch execution success. Confirm transaction prompts on targeted smartphone",
        "checkout_request_id": transaction.checkout_request_id,
        "merchant_request_id": transaction.merchant_request_id
    }

@router.post("/v1/mpesa-callback", status_code=status.HTTP_200_OK)
async def process_mpesa_asynchronous_callback(
    payload: MpesaCallbackPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 5 & 6 Flow: Receives transaction settlement callback vectors asynchronously from Safaricom API.

    Verifies tracking IDs, audits internal parameters, and triggers downstream premium tier upgrades.
    """
    callback_data = payload.Body.stkCallback
    logger.info(f"Asynchronous Callback Event payload processing trigger: {callback_data.CheckoutRequestID}")

    # Fetch corresponding transaction layer record inside current isolation state
    stmt = select(PaymentTransaction).where(PaymentTransaction.checkout_request_id == callback_data.CheckoutRequestID)
    execution_context = await db.execute(stmt)
    transaction = execution_context.scalar_one_or_none()

    if not transaction:
        logger.error(f"Orphan checkout callbacks routing signature match failure: {callback_data.CheckoutRequestID}")
        return {"ResultCode": 0, "ResultDesc": "Callback Handled Successfully"} # Always acknowledge cleanly to Safaricom to prevent loops

    transaction.raw_callback_payload = payload.model_dump()

    # Intercept cancellation loops or customer transaction processing drop errors
    if callback_data.ResultCode != 0:
        transaction.status = TransactionStatus.FAILED
        transaction.failure_reason = callback_data.ResultDesc
        db.add(transaction)
        await db.flush()
        return {"ResultCode": 0, "ResultDesc": "Failure trace processed successfully"}

    # Extract dynamic payload variables map out of the metadata arrays
    metadata_items = callback_data.CallbackMetadata.Item if callback_data.CallbackMetadata else []
    extracted_metadata = {item.Name: item.Value for item in metadata_items if item.Value is not None}

    transaction.mpesa_receipt_number = str(extracted_metadata.get("MpesaReceiptNumber"))
    transaction.status = TransactionStatus.COMPLETED
    db.add(transaction)

    # UNLOCK PREMIUM ACCOUNT NODE FLOW STEP 6
    sub_stmt = select(PremiumSubscription).where(PremiumSubscription.user_id == transaction.user_id)
    sub_context = await db.execute(sub_stmt)
    subscription = sub_context.scalar_one_or_none()

    now_utc = datetime.now(timezone.utc)
    extended_validity_period = timedelta(days=30) # Fixed structural default specification standard bounds tier logic

    if subscription and subscription.expires_at > now_utc:
        subscription.expires_at += extended_validity_period
    else:
        if not subscription:
            subscription = PremiumSubscription(user_id=transaction.user_id)
        subscription.expires_at = now_utc + extended_validity_period
        subscription.is_active = True

    db.add(subscription)
    await db.flush()

    logger.info(f"Unlocked Premium features for User Context: {transaction.user_id} with reference ID {transaction.mpesa_receipt_number}")
    return {"ResultCode": 0, "ResultDesc": "Ledger states and service vectors updated safely"}

@router.get("/history", response_model=list[TransactionOut])
async def get_my_transaction_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches list trace entries recorded against active account identities."""
    stmt = select(PaymentTransaction).where(PaymentTransaction.user_id == current_user.id).order_by(PaymentTransaction.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/transactions/{transaction_id}/refund", response_model=TransactionOut, dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def issue_transaction_refund(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Administrative override logic enabling manual or triggered financial reversals logs processing constraints."""
    stmt = select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
    res = await db.execute(stmt)
    transaction = res.scalar_one_or_none()

    if not transaction or transaction.status != TransactionStatus.COMPLETED:
        raise AppBaseException("Target ledger entries incompatible with requested execution operations rules", 400)

    transaction.status = TransactionStatus.REFUNDED
    db.add(transaction)

    # Revoke or adjust sub levels matching refund flows
    sub_stmt = select(PremiumSubscription).where(PremiumSubscription.user_id == transaction.user_id)
    sub_res = await db.execute(sub_stmt)
    subscription = sub_res.scalar_one_or_none()
    if subscription:
        subscription.is_active = False # Immediately terminate profile permissions mapping vector updates
        db.add(subscription)

    await db.flush()
    return transaction
