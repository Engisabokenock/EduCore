import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Text, DateTime, Numeric, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, pg_enum


class ExtendedResourceType(str, Enum):
    EXAM = "exam"
    NOTE = "note"
    WORKSHEET = "worksheet"
    QUIZ = "quiz"
    PAST_PAPER = "past_paper"
    MARKING_SCHEME = "marking_scheme"
    LESSON_PLAN = "lesson_plan"
    SCHEME_OF_WORK = "scheme_of_work"
    ASSIGNMENT = "assignment"
    HOLIDAY_ASSIGNMENT = "holiday_assignment"
    REVISION_PAPER = "revision_paper"
    VIDEO = "video"
    AUDIO = "audio"
    PRESENTATION = "presentation"
    OTHER = "other"


class WorkflowApprovalState(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class AssetVisibilityScope(str, Enum):
    PUBLIC = "public"
    REGISTERED = "registered"
    PREMIUM = "premium"
    PRIVATE = "private"
    SCHOOL = "school"


class PortalResource(Base):
    __tablename__ = "portal_resources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[ExtendedResourceType] = mapped_column(pg_enum(ExtendedResourceType), nullable=False, index=True)

    grade_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cbc_grades.id", ondelete="RESTRICT"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cbc_subjects.id", ondelete="RESTRICT"), nullable=False)
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cbc_topics.id", ondelete="SET NULL"), nullable=True)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)

    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(10), nullable=False)

    is_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    requires_subscription: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    visibility: Mapped[AssetVisibilityScope] = mapped_column(pg_enum(AssetVisibilityScope), default=AssetVisibilityScope.PREMIUM, nullable=False)
    approval_state: Mapped[WorkflowApprovalState] = mapped_column(pg_enum(WorkflowApprovalState), default=WorkflowApprovalState.DRAFT, nullable=False, index=True)

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    owner: Mapped["User"] = relationship(lazy="joined", foreign_keys=[owner_id])
    school: Mapped[Optional["School"]] = relationship(lazy="select")

    __table_args__ = (
        Index("ix_resources_permission_lookup", "approval_state", "visibility", "owner_id"),
    )
