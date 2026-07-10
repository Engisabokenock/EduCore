import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, DateTime, Enum as SQLEnum, Boolean, ForeignKey, Table, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

# Immutable Many-to-Many Association Ledger tracking Permission Matrix Allocations
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
)

class UserRole(str, Enum):
    # Advanced Role Hierarchy: separates business operations (Admin) from
    # system controls (Super Admin). SCHOOL_ADMIN is scoped to institutional
    # boundaries. Remaining roles map to classroom/consumer contexts.
    SUPER_ADMIN = "super_admin"  # Platform Owner - Complete Absolute Privilege
    ADMIN = "admin"              # Business Administrator - Complete Operations Coverage
    SCHOOL_ADMIN = "school_admin"# Institutional Principal - Scope Boundaries Enforced
    TEACHER = "teacher"          # Educator - Classroom Domain Context Mapping
    PARENT = "parent"            # External Monitor - Scoped Child Traversal Maps
    STUDENT = "student"          # Standard Client Consumer - Read Asset Vectors Only

class DynamicPermission(str, Enum):
    # Core Infrastructure Privilege Matrix Boundaries (Reserved for Super Admin)
    MANAGE_ADMINS = "manage_admins"
    MANAGE_SECURITY = "manage_security"
    MANAGE_SYSTEM = "manage_system"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_ROLES = "manage_roles"

    # Operational & Business Management Infrastructure Matrix (Shared Access Layer)
    MANAGE_USERS = "manage_users"
    MANAGE_RESOURCES = "manage_resources"
    MANAGE_PAYMENTS = "manage_payments"
    MANAGE_REVIEWS = "manage_reviews"
    MANAGE_NOTIFICATIONS = "manage_notifications"
    MANAGE_MARKETING = "manage_marketing"
    MANAGE_REPORTS = "manage_reports"
    MANAGE_SCHOOLS = "manage_schools"
    MANAGE_TEACHERS = "manage_teachers"
    MANAGE_STUDENTS = "manage_students"
    MANAGE_SUBSCRIPTIONS = "manage_subscriptions"
    MANAGE_AI = "manage_ai"
    MANAGE_SETTINGS = "manage_settings"

class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[DynamicPermission] = mapped_column(SQLEnum(DynamicPermission), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[UserRole] = mapped_column(String(50), unique=True, index=True, nullable=False)

    # Relationships with eager collection loading
    permissions: Mapped[List[Permission]] = relationship(
        secondary=role_permissions, lazy="selectin"
    )

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    role: Mapped[Role] = relationship(lazy="selectin")
    profile: Mapped[Profile] = relationship(back_populates="user")
    sessions: Mapped[List[UserSession]] = relationship(back_populates="user")

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(512), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=True)
    # JSONB used so metadata_fields can store dicts without PostgreSQL type errors.
    # Previously this was String, which broke registration inserts passing {}.
    metadata_fields: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False) # Stores custom preferences / regional school tags

    user: Mapped[User] = relationship(back_populates="profile")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    user_agent: Mapped[str] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped[User] = relationship(back_populates="sessions")

