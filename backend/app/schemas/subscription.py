import uuid
from datetime import datetime
from typing import Optional, List
import json
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.subscription import PlanTier, SubscriptionState

class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    tier: PlanTier
    price: float
    duration_days: int
    is_available: bool
    description: Optional[str] = None
    features: List[str] = []
    is_featured: bool = False
    sort_order: int = 0

    @field_validator("features", mode="before")
    @classmethod
    def parse_features(cls, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return [item.strip() for item in value.split(",") if item.strip()]
        if value is None:
            return []
        return value

class UserSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    plan: SubscriptionPlanResponse
    status: SubscriptionState
    auto_renew: bool
    current_period_start: datetime
    current_period_end: datetime
    grace_period_end: Optional[datetime]
    has_access: bool = False

class TriggerSubscriptionRenewal(BaseModel):
    plan_id: uuid.UUID
    phone_number: str = Field(..., description="Safaricom number, e.g. 0712345678")

    @field_validator("phone_number")
    @classmethod
    def _normalize_phone(cls, value: str) -> str:
        from app.schemas.payment import normalize_kenyan_msisdn
        return normalize_kenyan_msisdn(value)
