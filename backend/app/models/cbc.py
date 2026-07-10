import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, ForeignKey, Text, Enum as SQLEnum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class ResourceType(str, Enum):
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    INTERACTIVE = "interactive"

class Grade(Base):
    __tablename__ = "cbc_grades"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    curriculum: Mapped[str] = mapped_column(String(20), default="CBC", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(default=0, nullable=False)

    # Cascade relationships downstream
    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="grade", cascade="all, delete-orphan", lazy="selectin"
    )

class Subject(Base):
    __tablename__ = "cbc_subjects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    grade_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cbc_grades.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    icon: Mapped[str] = mapped_column(String(10), nullable=True)
    color: Mapped[str] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(default=0, nullable=False)

    grade: Mapped[Grade] = relationship(back_populates="subjects")
    topics: Mapped[list["Topic"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", lazy="selectin"
    )

class Topic(Base):
    __tablename__ = "cbc_topics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cbc_subjects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    ordering: Mapped[int] = mapped_column(default=0, nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    subject: Mapped[Subject] = relationship(back_populates="topics")
    learning_outcomes: Mapped[list["LearningOutcome"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan", lazy="selectin"
    )
    resources: Mapped[list["CurriculumResource"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan", lazy="selectin"
    )

class LearningOutcome(Base):
    __tablename__ = "cbc_learning_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cbc_topics.id", ondelete="CASCADE"), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False) # e.g., "Learner should be able to count objects up to 50"
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=True)

    topic: Mapped[Topic] = relationship(back_populates="learning_outcomes")

class CurriculumResource(Base):
    __tablename__ = "cbc_resources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cbc_topics.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    resource_type: Mapped[ResourceType] = mapped_column(SQLEnum(ResourceType), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False) # Maps to Cloudflare R2 links
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    topic: Mapped[Topic] = relationship(back_populates="resources")
