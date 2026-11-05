"""Platform activity log: an append-only record of who did what, when and from where."""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ActivityCategory(str, Enum):
    AUTH = "auth"            # sign-in, sign-out, failed logins, password changes
    ACCOUNT = "account"      # registration, profile changes, account deletion
    APPROVAL = "approval"    # teacher / admin applications and their review
    ADMIN = "admin"          # staff actions on users, roles, content and money
    PAYMENT = "payment"      # checkouts, settlements, refunds
    DOWNLOAD = "download"    # resource downloads
    CONTENT = "content"      # resource and curriculum changes
    REQUEST = "request"      # any other state-changing API call


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    # Who. The e-mail and role are snapshotted so the trail survives account changes.
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # What. Categories and actions are plain strings so new events need no migration.
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Where from.
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    http_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_activity_logs_category_time", "category", "occurred_at"),
        Index("ix_activity_logs_actor_time", "actor_id", "occurred_at"),
    )
