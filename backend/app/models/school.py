import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Text, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class AssignmentStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    GRADED = "graded"

class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    registration_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    classrooms: Mapped[list["Classroom"]] = relationship(back_populates="school", cascade="all, delete-orphan", lazy="select")

class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    grade_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cbc_grades.id", ondelete="RESTRICT"), nullable=False)
    stream_name: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., "North", "Blue"
    academic_year: Mapped[int] = mapped_column(nullable=False, index=True) # e.g., 2026

    # Staffing Vector Pointers
    class_teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    school: Mapped[School] = relationship(back_populates="classrooms")
    class_teacher: Mapped[Optional["User"]] = relationship(lazy="joined", foreign_keys=[class_teacher_id])
    enrollments: Mapped[list["ClassroomEnrollment"]] = relationship(back_populates="classroom", cascade="all, delete-orphan", lazy="select")
    assignments: Mapped[list["ClassAssignment"]] = relationship(back_populates="classroom", cascade="all, delete-orphan", lazy="select")

    __table_args__ = (
        Index("ux_school_grade_stream_year", "school_id", "grade_id", "stream_name", "academic_year", unique=True),
    )

class ClassroomEnrollment(Base):
    """Maps students and structural profiles down to distinct classrooms."""
    __tablename__ = "classroom_enrollments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    classroom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    classroom: Mapped[Classroom] = relationship(back_populates="enrollments")
    student: Mapped["User"] = relationship(lazy="joined", foreign_keys=[student_id])

    __table_args__ = (
        Index("ux_classroom_student", "classroom_id", "student_id", unique=True),
    )

class ClassAssignment(Base):
    __tablename__ = "class_assignments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    classroom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cbc_subjects.id", ondelete="RESTRICT"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_score: Mapped[int] = mapped_column(default=100, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    classroom: Mapped[Classroom] = relationship(back_populates="assignments")
    teacher: Mapped["User"] = relationship(lazy="select", foreign_keys=[teacher_id])
    submissions: Mapped[list["AssignmentSubmission"]] = relationship(back_populates="assignment", cascade="all, delete-orphan", lazy="select")

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_assignments.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Asset Pointers
    submission_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachment_file_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True) # Cloudflare R2 Upload link

    # Grading Parameters
    status: Mapped[AssignmentStatus] = mapped_column(SQLEnum(AssignmentStatus), default=AssignmentStatus.PENDING, nullable=False)
    score_achieved: Mapped[Optional[float]] = mapped_column(nullable=True)
    teacher_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    assignment: Mapped[ClassAssignment] = relationship(back_populates="submissions")
    student: Mapped["User"] = relationship(lazy="joined", foreign_keys=[student_id])

    __table_args__ = (
        Index("ux_assignment_student", "assignment_id", "student_id", unique=True),
    )
