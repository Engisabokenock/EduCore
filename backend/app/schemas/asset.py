import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.asset import ExtendedResourceType, WorkflowApprovalState, AssetVisibilityScope
import json


class ResourceUploadPayload(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    category: ExtendedResourceType
    grade_id: uuid.UUID
    subject_id: uuid.UUID
    topic_id: Optional[uuid.UUID] = None
    school_id: Optional[uuid.UUID] = None
    file_url: str = Field(..., max_length=512)
    file_extension: str = Field(..., min_length=2, max_length=10)
    is_free: bool = False
    price: float = Field(default=0.00, ge=0.00)
    requires_subscription: bool = True
    visibility: AssetVisibilityScope = AssetVisibilityScope.PREMIUM


class MetadataUpdatePayload(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ExtendedResourceType] = None
    is_free: Optional[bool] = None
    price: Optional[float] = None
    requires_subscription: Optional[bool] = None
    visibility: Optional[AssetVisibilityScope] = None


class ResourceModerationAction(BaseModel):
    target_state: WorkflowApprovalState = Field(..., description="Action mappings: 'approved', 'rejected', 'published'")
    rejection_notes: Optional[str] = None


class UnifiedResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str]
    category: ExtendedResourceType
    file_extension: str
    is_free: bool
    price: float
    requires_subscription: bool
    visibility: AssetVisibilityScope
    approval_state: WorkflowApprovalState
    owner_id: uuid.UUID
    created_at: datetime
