import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.school import AssignmentStatus

class SchoolCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    registration_code: str = Field(..., min_length=3, max_length=100)
    address: Optional[str] = None

class SchoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    registration_code: str
    address: Optional[str]
    is_active: bool
    created_at: datetime

class ClassroomCreateRequest(BaseModel):
    grade_id: uuid.UUID
    stream_name: str = Field(..., min_length=1, max_length=50)
    academic_year: int = Field(..., ge=2020, le=2100)
    class_teacher_id: Optional[uuid.UUID] = None

class ClassroomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    school_id: uuid.UUID
    grade_id: uuid.UUID
    stream_name: str
    academic_year: int
    class_teacher_id: Optional[uuid.UUID]

class AssignmentCreateRequest(BaseModel):
    subject_id: uuid.UUID
    title: str = Field(..., min_length=3, max_length=255)
    instructions: str = Field(..., min_length=5)
    due_date: datetime
    max_score: int = Field(default=100, gt=0)

class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    classroom_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    title: str
    instructions: str
    due_date: datetime
    max_score: int
    created_at: datetime

class GradeAssignmentRequest(BaseModel):
    score_achieved: float = Field(..., ge=0)
    teacher_feedback: Optional[str] = None
