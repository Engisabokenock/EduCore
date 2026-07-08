import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

class InitiateStkPushRequest(BaseModel):
    phone_number: str = Field(..., description="Safaricom phone number formatted as 2547XXXXXXXX or 07XXXXXXXX")
    amount: float = Field(..., gt=0, description="Amount in Kenyan Shillings (KES)")

    @field_validator("phone_number")
    @classmethod
    def sanitize_phone_number(cls, v: str) -> str:
        clean = re.sub(r"\D", "", v)
        if clean.startswith("07") or clean.startswith("01"):
            clean = "254" + clean[1:]
        elif clean.startswith("7") or clean.startswith("1"):
            clean = "254" + clean
        if not re.match(r"^254(7|1)\d{8}$", clean):
            raise ValueError("Invalid Safaricom phone number structure schema pattern alignment")
        return clean

class StkPushResponse(BaseModel):
    success: bool
    message: str
    checkout_request_id: str
    merchant_request_id: str

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    amount: float
    phone_number: str
    status: str
    checkout_request_id: str
    mpesa_receipt_number: Optional[str] = None
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
