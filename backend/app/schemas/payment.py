import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

def normalize_kenyan_msisdn(value: str) -> str:
    """Accept 07XX/01XX/7XX/+2547XX formats and return 2547XXXXXXXX / 2541XXXXXXXX."""
    clean = re.sub(r"\D", "", value or "")
    if clean.startswith("0") and len(clean) == 10:
        clean = "254" + clean[1:]
    elif len(clean) == 9 and clean[0] in "71":
        clean = "254" + clean
    if not re.fullmatch(r"254(7|1)\d{8}", clean):
        raise ValueError("Enter a valid Safaricom number, e.g. 0712345678")
    return clean


class InitiateStkPushRequest(BaseModel):
    """Checkout request. The amount is derived from the plan on the server."""
    plan_id: uuid.UUID
    phone_number: str = Field(..., description="Safaricom number, e.g. 0712345678 or 254712345678")

    @field_validator("phone_number")
    @classmethod
    def sanitize_phone_number(cls, v: str) -> str:
        return normalize_kenyan_msisdn(v)


class StkPushResponse(BaseModel):
    success: bool
    message: str
    checkout_request_id: str
    merchant_request_id: str
    amount: float


class PaymentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    checkout_request_id: str
    status: str
    amount: float
    mpesa_receipt_number: Optional[str] = None
    failure_reason: Optional[str] = None

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    amount: float
    phone_number: str
    status: str
    checkout_request_id: str
    mpesa_receipt_number: Optional[str] = None
    failure_reason: Optional[str] = None
    plan_id: Optional[uuid.UUID] = None
    created_at: datetime

# M-Pesa Callback Structural Ingestion Schemas (Direct mapping of Daraja JSON Payload specifications)
class CallbackItem(BaseModel):
    Name: str
    Value: Optional[Any] = None

class CallbackItemWrapper(BaseModel):
    Item: list[CallbackItem]

class StkCallbackDetails(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Optional[CallbackItemWrapper] = None

class MpesaCallbackBody(BaseModel):
    stkCallback: StkCallbackDetails

class MpesaCallbackPayload(BaseModel):
    Body: MpesaCallbackBody
