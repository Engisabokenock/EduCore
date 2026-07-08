from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import Optional
from app.models.cbc import ResourceType

# --- Resource Schemas ---
class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    resource_type: ResourceType
    url: str = Field(..., min_length=10, max_length=512)

class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    resource_type: ResourceType
    url: str

# --- Learning Outcome Schemas ---
class LearningOutcomeCreate(BaseModel):
    statement: str = Field(..., min_length=5)
    code: Optional[str] = Field(None, max_length=50)

class LearningOutcomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    statement: str
    code: Optional[str]

# --- Topic Schemas ---
class TopicCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    ordering: int = Field(default=0, ge=0)

class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    ordering: int
    learning_outcomes: list[LearningOutcomeOut]
    resources: list[ResourceOut]

# --- Subject Schemas ---
class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=30)
    description: Optional[str] = None

class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    code: str
    description: Optional[str]

class SubjectDetailOut(SubjectOut):
    topics: list[TopicOut]

# --- Grade Schemas ---
class GradeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None

class GradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    code: str
    description: Optional[str]

class GradeDetailOut(GradeOut):
    subjects: list[SubjectOut]
