import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.review import ReviewModerationStatus

class ReviewCreateRequest(BaseModel):
    resource_id: uuid.UUID
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

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Gracefully handle profile unboxing safely during model transitions
        return cls(
            id=obj.id,
            full_name=obj.profile.full_name if (hasattr(obj, "profile") and obj.profile) else "Anonymous Learner",
            avatar_url=obj.profile.avatar_url if (hasattr(obj, "profile") and obj.profile) else None
        )

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
