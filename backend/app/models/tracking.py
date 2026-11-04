import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class DownloadLog(Base):
    __tablename__ = "download_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_resources.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Telemetry and Location Vectors
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False) # Supports both IPv4 and IPv6 strings
    device_fingerprint: Mapped[str] = mapped_column(String(512), nullable=False) # Full User-Agent metadata storage
    country_code: Mapped[str] = mapped_column(String(3), default="KE", nullable=False) # ISO Alpha-3 structure
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Composite Analytics Optimization Indices
    __table_args__ = (
        Index("ix_downloads_user_timeline", "user_id", "downloaded_at"),
        Index("ix_downloads_resource_timeline", "resource_id", "downloaded_at"),
        Index("ix_downloads_ip_timeline", "ip_address", "downloaded_at"),
    )

    # Relationships
    resource: Mapped["AcademicResource"] = relationship(lazy="joined")
    user: Mapped[Optional["User"]] = relationship(lazy="select")
