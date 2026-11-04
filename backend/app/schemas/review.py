import uuid
from datetime import datetime
from typing import Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator
from app.models.review import ReviewModerationStatus

class ReviewCreateRequest(BaseModel):
    resource_id: uuid.UUID = Field(..., validation_alias=AliasChoices("resource_id", "resource"))
    rating: int = Field(..., ge=1, le=5, description="Star rating grading system constraint baseline")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional textual user context commentary feed")

class ReviewUpdateRequest(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)

class ReportAbuseRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=255, description="Context explanation reporting violation parameters")

class UserReviewerOut(BaseModel):
    id: uuid.UUID
    full_name: str
    avatar_url: Optional[str] = None

    # Overriding model_validate is bypassed for nested fields, so flatten the ORM user
    # in a "before" validator instead (otherwise every review response failed with 500).
    @model_validator(mode="before")
    @classmethod
    def _from_user(cls, obj):
        if isinstance(obj, dict):
            return obj
        profile = getattr(obj, "profile", None)
        return {
            "id": obj.id,
            "full_name": (profile.full_name if profile else None) or "EduCore learner",
            "avatar_url": profile.avatar_url if profile else None,
        }

class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    resource_id: uuid.UUID
    rating: int
    comment: Optional[str]
    moderation_status: ReviewModerationStatus
    is_reported: bool
    created_at: datetime
    updated_at: datetime
    user: UserReviewerOut
