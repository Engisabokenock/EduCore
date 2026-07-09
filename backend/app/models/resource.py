import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import String, ForeignKey, Text, Enum as SQLEnum, DateTime, Integer, Boolean, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class ResourceTypeVariant(str, Enum):
    REVISION_PAPER = "revision_paper"
    WORKSHEET = "worksheet"
    EXAM = "exam"
    MOCK_EXAM = "mock_exam"
    PAST_PAPER = "past_paper"
    LESSON_NOTE = "lesson_note"
    MARKING_SCHEME = "marking_scheme"
    SCHEME_OF_WORK = "scheme_of_work"
    LESSON_PLAN = "lesson_plan"

class AcademicTerm(int, Enum):
    TERM_1 = 1
    TERM_2 = 2
    TERM_3 = 3

# Many-to-Many Association Table for Resource Tagging
resource_tags = Table(
    "resource_tag_associations",
    Base.metadata,
    Column("resource_id", ForeignKey("academic_resources.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("content_tags.id", ondelete="CASCADE"), primary_key=True)
)

class ContentTag(Base):
    __tablename__ = "content_tags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

class AcademicResource(Base):
    __tablename__ = "academic_resources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Core CBC Hierarchical Matrix Mappings
    grade_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cbc_grades.id", ondelete="RESTRICT"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cbc_subjects.id", ondelete="RESTRICT"), nullable=False)
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cbc_topics.id", ondelete="SET NULL"), nullable=True)

    # Temporal Parameters
    term: Mapped[AcademicTerm] = mapped_column(SQLEnum(AcademicTerm), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Storage Pointers (Cloudflare R2 Integration Engine Targets)
    pdf_url: Mapped[str] = mapped_column(String(512), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Classification & Access Vector Gates
    type_variant: Mapped[ResourceTypeVariant] = mapped_column(SQLEnum(ResourceTypeVariant), nullable=False, index=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Publishing Workflows
    scheduled_publish_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Telemetry and Engagement Tracking Metrics
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Creator Audit Trails
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Database Mapped Node Target Relationships
    created_by: Mapped["User"] = relationship(lazy="raise")
    grade: Mapped["Grade"] = relationship(lazy="selectin")
    subject: Mapped["Subject"] = relationship(lazy="selectin")
    topic: Mapped[Optional["Topic"]] = relationship(lazy="selectin")
    tags: Mapped[list[ContentTag]] = relationship(secondary=resource_tags, lazy="selectin")

