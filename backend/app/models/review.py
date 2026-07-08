import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Integer, Boolean, Text, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class ReviewModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ResourceReview(Base):
    __tablename__ = "resource_reviews"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_resources.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Content Metric Vectors
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # Enforced check constraint 1 to 5 stars
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Moderation Infrastructure Parameters
    moderation_status: Mapped[ReviewModerationStatus] = mapped_column(
        SQLEnum(ReviewModerationStatus), default=ReviewModerationStatus.PENDING, nullable=False, index=True
    )
    is_reported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    report_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    moderated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(lazy="joined", foreign_keys=[user_id])
    resource: Mapped["AcademicResource"] = relationship(lazy="raise")

    __table_args__ = (
        Index("ux_user_resource_review", "user_id", "resource_id", unique=True),
    )
