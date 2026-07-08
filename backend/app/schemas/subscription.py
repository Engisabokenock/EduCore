import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.subscription import PlanTier, SubscriptionState

class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    tier: PlanTier
    price: float
    duration_days: int
    is_available: bool

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

class TriggerSubscriptionRenewal(BaseModel):
    plan_id: uuid.UUID
    phone_number: str = Field(..., pattern=r"^254(7|1)\d{8}$", description="Safaricom dynamic billing phone context")
