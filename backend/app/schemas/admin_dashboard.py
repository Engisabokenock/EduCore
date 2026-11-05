import uuid
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from app.models.base import AccountApprovalStatus, UserRole
from app.models.payment import TransactionStatus

# --- USER CONTROL CONTROL GRID ---
class AdminUserSearchPayload(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    approval_status: Optional[AccountApprovalStatus] = None
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


class AdminDashboardStats(BaseModel):
    total_users: int
    active_subscriptions: int
    total_revenue: float
    pending_reviews: int
    total_resources: int
    total_schools: int


# --- STAFF LISTINGS ---
from datetime import datetime  # noqa: E402


class AdminResourceRow(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    type_variant: str
    grade: str
    subject: str
    term: int
    year: int
    is_premium: bool
    status: str
    views_count: int
    downloads_count: int
    created_at: datetime
    published_at: Optional[datetime] = None


class AdminResourcePage(BaseModel):
    items: List[AdminResourceRow]
    total: int
    page: int
    page_size: int


class AdminSubscriptionRow(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: str
    user_name: Optional[str] = None
    plan_name: str
    status: str
    auto_renew: bool
    current_period_start: datetime
    current_period_end: datetime
    is_current: bool


class AdminSubscriptionPage(BaseModel):
    items: List[AdminSubscriptionRow]
    total: int
    page: int
    page_size: int
