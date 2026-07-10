import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.notification import NotificationChannel, NotificationEvent

class PreferenceItem(BaseModel):
    event_type: NotificationEvent
    channel: NotificationChannel
    is_enabled: bool

class UpdatePreferencesRequest(BaseModel):
    preferences: list[PreferenceItem]

class PreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_type: NotificationEvent
    channel: NotificationChannel
    is_enabled: bool

class NotificationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    notification_type: str
    channel: str
    title: str
    body: str
    data: Optional[dict] = None
    is_read: bool
    sent_at: datetime
    read_at: Optional[datetime] = None
    created_at: datetime
