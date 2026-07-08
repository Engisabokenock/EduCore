import uuid
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.resource import ResourceTypeVariant, AcademicTerm
from app.schemas.resource import ResourceOut

class SearchSortOrder(str, Enum):
    NEWEST = "newest"
    POPULARITY = "popularity"
    MOST_DOWNLOADED = "most_downloaded"

class SearchFilterPayload(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    # Core Academic Filtration Nodes
    grade_id: Optional[uuid.UUID] = Field(None, description="Unique identifier for CBC Grade level filtration")
    subject_id: Optional[uuid.UUID] = Field(None, description="Unique identifier for CBC Subject filtration")
    topic_id: Optional[uuid.UUID] = Field(None, description="Unique identifier for CBC Topic filtration")

    # Metadata Attribute Vector Filters
    keyword: Optional[str] = Field(None, min_length=2, max_length=100, description="Full text index search token pattern")
    is_premium: Optional[bool] = Field(None, description="Toggle filter for free vs subscription tier files")
    type_variant: Optional[ResourceTypeVariant] = Field(None, description="Filtration targeting specific file classification types")
    year: Optional[int] = Field(None, ge=2020, le=2100, description="Calendar year academic parameter target matching")
    term: Optional[AcademicTerm] = Field(None, description="Academic period term block alignment matches")

    # Pagination Control Specifications
    page: int = Field(default=1, ge=1, description="Sequential current index viewing segment page slice tracker")
    page_size: int = Field(default=20, ge=1, le=100, description="Volumetric count scale slice bound size parameter per execution")

    # Sorting Order Determinations
    sort_by: SearchSortOrder = Field(default=SearchSortOrder.NEWEST, description="Target sorting execution pattern variant")

class SearchPaginationMetadata(BaseModel):
    total_records: int
    total_pages: int
    current_page: int
    page_size: int
    has_next: bool
    has_previous: bool

class PaginatedSearchResults(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    metadata: SearchPaginationMetadata
    results: list[ResourceOut]
