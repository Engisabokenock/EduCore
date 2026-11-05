import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import RoleChecker, get_current_user
from app.core.database import get_db
from app.models.base import User, UserRole
from app.models.payment import PaymentTransaction
from app.schemas.payment import (
    InitiateStkPushRequest,
    MpesaCallbackPayload,
    PaymentStatusResponse,
    StkPushResponse,
    TransactionOut,
)
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["M-Pesa Transaction Lifecycle Ledger Core Ecosystem"])
logger = logging.getLogger("educore.callbacks")


@router.post("/buy-premium", response_model=StkPushResponse, status_code=status.HTTP_202_ACCEPTED)
@router.post("/checkout", response_model=StkPushResponse, status_code=status.HTTP_202_ACCEPTED)
async def initiate_premium_purchase(
    payload: InitiateStkPushRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send an M-Pesa STK prompt for the chosen plan. Poll /payments/status/{id} afterwards."""
    transaction = await payment_service.start_checkout(db, current_user, payload.plan_id, payload.phone_number)
    return {
        "success": True,
        "message": "Check your phone and enter your M-Pesa PIN to complete the payment.",
        "checkout_request_id": transaction.checkout_request_id,
        "merchant_request_id": transaction.merchant_request_id,
        "amount": float(transaction.amount),
    }


@router.post("/mpesa/callback", status_code=status.HTTP_200_OK, include_in_schema=False)
@router.post("/v1/mpesa-callback", status_code=status.HTTP_200_OK, include_in_schema=False)
async def process_mpesa_asynchronous_callback(
    payload: MpesaCallbackPayload,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Daraja settlement webhook. Authenticated by the ?token= shared secret."""
    return await payment_service.handle_callback(db, payload, token)


@router.get("/status/{checkout_request_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    checkout_request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Polling endpoint for the checkout UI; reconciles with Daraja if the callback is late."""
    return await payment_service.get_checkout_status(db, current_user, checkout_request_id)


@router.get("/history", response_model=list[TransactionOut])
async def get_my_transaction_history(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(PaymentTransaction)
        .where(PaymentTransaction.user_id == current_user.id)
        .order_by(PaymentTransaction.created_at.desc())
        .limit(100)
    )
    return (await db.execute(stmt)).scalars().all()


@router.post("/transactions/{transaction_id}/refund", response_model=TransactionOut)
async def issue_transaction_refund(
    transaction_id: uuid.UUID,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Mark a completed payment refunded and revoke the access it bought."""
    return await payment_service.refund(db, transaction_id, actor=current_user)
