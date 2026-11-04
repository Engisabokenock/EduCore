import uuid
from datetime import datetime
from typing import Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
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
    notification_type: str = Field(validation_alias=AliasChoices("notification_type", "event_type"))
    channel: str
    title: str
    body: str
    data: Optional[dict] = None
    is_read: bool
    sent_at: datetime
    read_at: Optional[datetime] = None
    created_at: datetime = Field(validation_alias=AliasChoices("created_at", "sent_at"))

    @field_validator("notification_type", "channel", mode="before")
    @classmethod
    def _enum_value(cls, value):
        return getattr(value, "value", value)
