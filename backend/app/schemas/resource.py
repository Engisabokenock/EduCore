from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.resource import ResourceTypeVariant, AcademicTerm

class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    grade_id: UUID
    subject_id: UUID
    topic_id: Optional[UUID] = None
    term: AcademicTerm
    year: int = Field(..., ge=2020, le=2100)
    pdf_url: str = Field(..., max_length=512)
    thumbnail_url: Optional[str] = Field(None, max_length=512)
    type_variant: ResourceTypeVariant
    is_premium: bool = False
    scheduled_publish_at: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)

class ResourceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    grade_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    term: Optional[AcademicTerm] = None
    year: Optional[int] = Field(None, ge=2020, le=2100)
    pdf_url: Optional[str] = Field(None, max_length=512)
    thumbnail_url: Optional[str] = Field(None, max_length=512)
    type_variant: Optional[ResourceTypeVariant] = None
    is_premium: Optional[bool] = None
    scheduled_publish_at: Optional[datetime] = None

class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str

class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: Optional[str]
    grade_id: UUID
    subject_id: UUID
    topic_id: Optional[UUID]
    term: AcademicTerm
    year: int
    pdf_url: str
    thumbnail_url: Optional[str]
    type_variant: ResourceTypeVariant
    is_premium: bool
    is_published: bool
    is_archived: bool
    scheduled_publish_at: Optional[datetime]
    views_count: int
    downloads_count: int
    created_by_id: UUID
    created_at: datetime
    tags: list[TagOut]
