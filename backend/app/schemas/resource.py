from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.resource import ResourceTypeVariant, AcademicTerm

class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    slug: str = Field(..., min_length=3, max_length=255)
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

class PaginatedResourceResponse(BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    total_pages: int
    current_page: int
    results: list[ResourceOut]

class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str

class GradeInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str

class SubjectInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str

class TopicInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str

class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: UUID
    title: str
    description: Optional[str]
    slug: str
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
    published_at: Optional[datetime] = None
    views_count: int
    downloads_count: int
    created_by_id: UUID
    created_at: datetime
    grade: Optional[GradeInfo] = None
    subject: Optional[SubjectInfo] = None
    topic: Optional[TopicInfo] = None
    tags: list[TagOut]

    @property
    def view_count(self) -> int:
        return self.views_count

    @property
    def download_count(self) -> int:
        return self.downloads_count

    @property
    def file(self) -> str:
        return self.pdf_url

    @property
    def file_type(self) -> str:
        return self.type_variant.value

    @property
    def file_size(self) -> int:
        return 0
