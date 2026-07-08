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
    event_type: NotificationEvent
    channel: NotificationChannel
    recipient_address: str
    title: str
    body: str
    is_sent: bool
    failure_reason: Optional[str] = None
    sent_at: datetime
