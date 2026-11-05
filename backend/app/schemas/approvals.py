from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.auth import UserPublicSchema


# ── Account applications ─────────────────────────────────────────────────────

class ApplicationOut(UserPublicSchema):
    reviewed_at: Optional[str] = None
    reviewed_by_id: Optional[UUID] = None
    review_note: Optional[str] = None


class ApplicationPage(BaseModel):
    items: List[ApplicationOut]
    total: int
    page: int
    page_size: int


class ApplicationCounts(BaseModel):
    total: int
    by_role: Dict[str, int]


class ReviewDecision(BaseModel):
    note: Optional[str] = Field(None, max_length=500, description="Optional message shown to the applicant.")


# ── Activity log ─────────────────────────────────────────────────────────────

class ActivityEntryOut(BaseModel):
    id: UUID
    occurred_at: datetime
    actor_id: Optional[UUID] = None
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    category: str
    action: str
    summary: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    http_method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None


class ActivityPage(BaseModel):
    items: List[ActivityEntryOut]
    total: int
    page: int
    page_size: int


class ActivitySummary(BaseModel):
    window_hours: int
    total_events: int
    by_category: Dict[str, int]
    failed_logins: int
    active_users: int
    pending_approvals: int
