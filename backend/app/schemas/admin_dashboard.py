import uuid
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from app.models.base import UserRole
from app.models.resource import ResourceTypeVariant, AcademicTerm
from app.models.subscription import SubscriptionState, PlanTier
from app.models.payment import TransactionStatus

# --- USER CONTROL CONTROL GRID ---
class AdminUserSearchPayload(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    search_term: Optional[str] = Field(None, min_length=2, description="Targets email address match or full name text fields")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

class AdminUserUpdatePayload(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None

# --- TRANSACTION COMPLIANCE EXTRACTIONS ---
class AdminPaymentFilterPayload(BaseModel):
    status: Optional[TransactionStatus] = None
    phone_number: Optional[str] = None
    mpesa_receipt: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)

# --- CONFIGURATION MATRICES GLOBAL RULES ---
class SystemSettingsUpdatePayload(BaseModel):
    maintenance_mode: Optional[bool] = None
    daily_free_download_limit: Optional[int] = Field(None, ge=0)
    allowed_upload_extensions: Optional[List[str]] = None
    grace_period_duration_days: Optional[int] = Field(None, ge=1)
    mpesa_fallback_routing_active: Optional[bool] = None

class AdminBulkActionRequest(BaseModel):
    target_ids: List[uuid.UUID] = Field(..., min_length=1)
    action: str = Field(..., description="Action mappings: 'approve', 'reject', 'purge', 'archive', 'activate'")
