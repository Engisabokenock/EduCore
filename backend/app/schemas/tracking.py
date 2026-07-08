from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict
from app.schemas.resource import ResourceOut

class DownloadLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resource_id: UUID
    ip_address: str
    device_fingerprint: str
    country_code: str
    downloaded_at: datetime
    resource: Optional[ResourceOut] = None

class DownloadSummaryMetrics(BaseModel):
    total_downloads: int
    unique_users_count: int
    downloads_by_country: Dict[str, int]
    downloads_by_type: Dict[str, int]
