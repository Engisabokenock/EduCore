"""Commerce business logic — M-Pesa STK Push, subscriptions."""
import logging
import uuid
from datetime import timedelta
from decimal import Decimal

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction as db_transaction
from django.utils import timezone

from core.utils import sanitize_phone, generate_reference_code
from .models import Plan, Subscription, Payment, Coupon

logger = logging.getLogger("apps.commerce")

_MPESA_TOKEN_CACHE_KEY = "mpesa_access_token"
_MPESA_TOKEN_TTL = 3000  # 50 minutes — Safaricom tokens expire after 1 hour


def _get_mpesa_access_token() -> str:
    token = cache.get(_MPESA_TOKEN_CACHE_KEY)
    if token:
        return token
    base_url = (
        settings.MPESA_BASE_URL
        or "https://sandbox.safaricom.co.ke"
        if settings.MPESA_ENVIRONMENT == "sandbox"
        else settings.MPESA_BASE_URL
        or "https://api.safaricom.co.ke"
    )
    resp = requests.get(
        f"{base_url}/oauth/v1/generate?grant_type=client_credentials",
        auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
        timeout=10,
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    cache.set(_MPESA_TOKEN_CACHE_KEY, token, timeout=_MPESA_TOKEN_TTL)
    return token


def initiate_mpesa_stk_push(phone: str, amount: Decimal, reference: str, description: str) -> dict:
    import base64
    from datetime import datetime

    phone = sanitize_phone(phone)
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    passkey = settings.MPESA_PASSKEY
    shortcode = settings.MPESA_SHORTCODE
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()

    access_token = _get_mpesa_access_token()
    base_url = (
        settings.MPESA_BASE_URL
        or "https://sandbox.safaricom.co.ke"
        if settings.MPESA_ENVIRONMENT == "sandbox"
        else settings.MPESA_BASE_URL
        or "https://api.safaricom.co.ke"
    )
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": reference,
        "TransactionDesc": description,
    }
    resp = requests.post(
        f"{base_url}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def calculate_discounted_price(plan: Plan, coupon_code: str = "") -> Decimal:
    price = plan.price
    if not coupon_code:
        return price
    try:
        coupon = Coupon.objects.get(code=coupon_code.upper())
        if not coupon.is_valid():
            return price
        applicable = coupon.applicable_plans.all()
        if applicable.exists() and plan not in applicable:
            return price
        if coupon.discount_type == Coupon.DiscountType.PERCENT:
            discount = price * (coupon.discount_value / 100)
        else:
            discount = coupon.discount_value
        return max(price - discount, Decimal("0"))
    except Coupon.DoesNotExist:
        return price


def create_pending_payment(user, plan: Plan, phone: str, amount: Decimal) -> Payment:
    return Payment.objects.create(
        user=user,
        plan=plan,
        amount=amount,
        currency="KES",
        gateway=Payment.Gateway.MPESA,
        status=Payment.Status.PENDING,
        reference=generate_reference_code("PAY"),
        phone_number=phone,
    )


def activate_subscription(user, plan: Plan) -> Subscription:
    now = timezone.now()
    if plan.billing_cycle == Plan.BillingCycle.MONTHLY:
        expires = now + timedelta(days=30)
    elif plan.billing_cycle == Plan.BillingCycle.ANNUAL:
        expires = now + timedelta(days=365)
    else:
        expires = None  # Lifetime

    with db_transaction.atomic():
        Subscription.objects.select_for_update().filter(
            user=user, status=Subscription.Status.ACTIVE
        ).update(status=Subscription.Status.CANCELLED, cancelled_at=now)

        return Subscription.objects.create(
            user=user,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            started_at=now,
            expires_at=expires,
        )


def handle_mpesa_callback(payload: dict) -> None:
    """Process M-Pesa STK Push callback.

    Security model:
    - Caller (view) enforces IP allowlist before calling this function.
    - We look up payment by MerchantRequestID (set at STK-push time), NOT by
      loose phone-number matching, so a callback cannot activate the wrong user.
    - We validate amount matches what we requested.
    - We guard against duplicate callbacks via unique transaction_id.
    - The entire state transition runs inside an atomic block with
      select_for_update to prevent race conditions from concurrent callbacks.
    """
    try:
        stk = payload.get("Body", {}).get("stkCallback", {})
        merchant_request_id = stk.get("MerchantRequestID", "")
        result_code = stk.get("ResultCode")
        result_desc = stk.get("ResultDesc", "Unknown error")

        if result_code != 0:
            # Payment cancelled or timed out by user — mark as failed
            if merchant_request_id:
                Payment.objects.filter(
                    merchant_request_id=merchant_request_id,
                    status=Payment.Status.PENDING,
                ).update(
                    status=Payment.Status.FAILED,
                    error_message=result_desc,
                    raw_response=payload,
                )
            logger.warning("M-Pesa STK push failed [%s]: %s", merchant_request_id, result_desc)
            return

        items = {
            item["Name"]: item.get("Value")
            for item in stk.get("CallbackMetadata", {}).get("Item", [])
        }
        transaction_id = items.get("MpesaReceiptNumber") or ""
        amount = Decimal(str(items.get("Amount", 0)))

        if not transaction_id:
            logger.error("M-Pesa callback missing MpesaReceiptNumber — payload: %s", payload)
            return

        # Idempotency: reject callbacks that carry an already-processed receipt
        if Payment.objects.filter(transaction_id=transaction_id).exists():
            logger.info("Duplicate M-Pesa callback for receipt %s — skipping", transaction_id)
            return

        with db_transaction.atomic():
            qs = Payment.objects.select_for_update().filter(
                status=Payment.Status.PENDING,
                gateway=Payment.Gateway.MPESA,
            )

            payment = None
            if merchant_request_id:
                payment = qs.filter(merchant_request_id=merchant_request_id).first()

            if payment is None:
                logger.error(
                    "No pending MPESA payment for MerchantRequestID=%s (receipt=%s)",
                    merchant_request_id,
                    transaction_id,
                )
                return

            # Validate paid amount matches what we charged (tolerance: 1 cent)
            if abs(payment.amount - amount) > Decimal("0.01"):
                logger.error(
                    "Amount mismatch for payment %s: expected %s, received %s",
                    payment.reference,
                    payment.amount,
                    amount,
                )
                payment.status = Payment.Status.FAILED
                payment.error_message = (
                    f"Amount mismatch: expected KES {payment.amount}, received KES {amount}"
                )
                payment.raw_response = payload
                payment.save(update_fields=["status", "error_message", "raw_response"])
                return

            payment.status = Payment.Status.SUCCESS
            payment.transaction_id = transaction_id
            payment.paid_at = timezone.now()
            payment.raw_response = payload
            payment.save(update_fields=["status", "transaction_id", "paid_at", "raw_response"])

            if payment.plan:
                sub = activate_subscription(payment.user, payment.plan)
                payment.subscription = sub
                payment.save(update_fields=["subscription"])

    except Exception:
        logger.exception("Unhandled error processing M-Pesa callback")
