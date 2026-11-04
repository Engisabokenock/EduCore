import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, pg_enum

class PlanTier(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class SubscriptionState(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"         # Active access until end of current cycle; auto-renew disabled
    GRACE_PERIOD = "grace_period"   # Payment failed; limited duration retry state
    EXPIRED = "expired"           # Hard access termination state

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    tier: Mapped[PlanTier] = mapped_column(pg_enum(PlanTier), unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    duration_days: Mapped[int] = mapped_column(nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    features: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False)

    # Structural Status Configurations
    status: Mapped[SubscriptionState] = mapped_column(pg_enum(SubscriptionState), default=SubscriptionState.ACTIVE, nullable=False, index=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Dynamic Timeline Tracking Parameters
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    grace_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Database Mapped Node Target Relationships
    user: Mapped["User"] = relationship(lazy="raise")
    plan: Mapped[SubscriptionPlan] = relationship(lazy="joined")

    # Cron indexing optimization strategies
    __table_args__ = (
        Index("ix_user_subs_lifecycle", "status", "current_period_end"),
    )
