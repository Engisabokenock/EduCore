"""Safaricom Daraja (Lipa Na M-Pesa Online / STK Push) client."""
import asyncio
import base64
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

import httpx

from app.core.config import settings
from app.core.exceptions import AppBaseException, ServiceUnavailableError

logger = logging.getLogger("educore.payments")

# Daraja timestamps must be in Kenyan time (EAT, UTC+3) regardless of server timezone.
EAT = timezone(timedelta(hours=3))


class MpesaClient:
    """Thin, typed wrapper over the Daraja endpoints the platform uses."""

    _token: Optional[str] = None
    _token_expires_at: float = 0.0
    _token_lock = asyncio.Lock()

    def __init__(self):
        self.base_url = (
            "https://api.safaricom.co.ke"
            if settings.MPESA_ENVIRONMENT == "production"
            else "https://sandbox.safaricom.co.ke"
        )

    @staticmethod
    def _ensure_configured() -> None:
        if not settings.mpesa_configured:
            raise ServiceUnavailableError("M-Pesa payments are not configured on this server yet.")

    async def _get_auth_token(self) -> str:
        """OAuth token, cached until shortly before it expires (Daraja issues ~1h tokens)."""
        cls = type(self)
        if cls._token and time.monotonic() < cls._token_expires_at:
            return cls._token
        async with cls._token_lock:
            if cls._token and time.monotonic() < cls._token_expires_at:
                return cls._token
            credentials = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
            encoded = base64.b64encode(credentials.encode()).decode()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/oauth/v1/generate",
                    params={"grant_type": "client_credentials"},
                    headers={"Authorization": f"Basic {encoded}"},
                )
            if response.status_code != 200:
                logger.error("Daraja OAuth failed (%s): %s", response.status_code, response.text[:500])
                raise AppBaseException("Could not reach M-Pesa right now. Please try again.", 502)
            body = response.json()
            cls._token = body["access_token"]
            cls._token_expires_at = time.monotonic() + max(int(body.get("expires_in", 3599)) - 60, 60)
            return cls._token

    @staticmethod
    def _password(timestamp: str) -> str:
        source = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
        return base64.b64encode(source.encode()).decode()

    @staticmethod
    def callback_url() -> str:
        """Configured callback URL with the shared secret appended as ?token=..."""
        url = settings.MPESA_CALLBACK_URL or ""
        if not settings.MPESA_CALLBACK_SECRET:
            return url
        parts = urlparse(url)
        query = dict(parse_qsl(parts.query))
        query["token"] = settings.MPESA_CALLBACK_SECRET
        return urlunparse(parts._replace(query=urlencode(query)))

    async def send_stk_push(self, phone_number: str, amount: int, account_reference: str,
                            description: str = "EduCore") -> dict:
        """Prompt the customer's phone to authorise a payment."""
        self._ensure_configured()
        token = await self._get_auth_token()
        timestamp = datetime.now(EAT).strftime("%Y%m%d%H%M%S")
        is_till = settings.MPESA_TRANSACTION_TYPE == "CustomerBuyGoodsOnline"
        party_b = settings.MPESA_TILL_NUMBER if is_till and settings.MPESA_TILL_NUMBER else settings.MPESA_SHORTCODE

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": self._password(timestamp),
            "Timestamp": timestamp,
            "TransactionType": settings.MPESA_TRANSACTION_TYPE,
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": party_b,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url(),
            "AccountReference": account_reference[:12],
            "TransactionDesc": description[:13],
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
        body = self._json(response)
        if response.status_code != 200 or str(body.get("ResponseCode")) != "0":
            logger.error("STK push rejected (%s): %s", response.status_code, response.text[:500])
            message = body.get("errorMessage") or body.get("CustomerMessage") or "M-Pesa could not start the payment."
            raise AppBaseException(message, 502)
        return body

    async def query_stk_status(self, checkout_request_id: str) -> dict:
        """Ask Daraja for the authoritative result of an STK push."""
        self._ensure_configured()
        token = await self._get_auth_token()
        timestamp = datetime.now(EAT).strftime("%Y%m%d%H%M%S")
        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": self._password(timestamp),
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/mpesa/stkpushquery/v1/query",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
        return self._json(response)

    @staticmethod
    def _json(response: httpx.Response) -> dict:
        try:
            data = response.json()
            return data if isinstance(data, dict) else {}
        except ValueError:
            return {}
