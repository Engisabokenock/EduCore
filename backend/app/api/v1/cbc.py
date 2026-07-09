from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from app.core.database import get_db
from app.core.exceptions import AppBaseException
from app.api.deps import RoleChecker
from app.models.base import UserRole
from app.models.cbc import Grade, Subject, Topic, LearningOutcome, CurriculumResource
from app.schemas.cbc import (
    GradeCreate, GradeOut, GradeDetailOut,
    SubjectCreate, SubjectDetailOut,
    TopicCreate, TopicOut,
    LearningOutcomeCreate, LearningOutcomeOut,
    ResourceCreate, ResourceOut
)

router = APIRouter(prefix="/academic", tags=["CBC Curriculum Management Vector"])

# Structural Enforcement Guardrails
admin_protect = Depends(RoleChecker([UserRole.ADMIN]))
educator_or_admin_protect = Depends(RoleChecker([UserRole.ADMIN, UserRole.TEACHER]))

# --- GRADE ENDPOINTS ---
@router.post("/grades", response_model=GradeOut, status_code=status.HTTP_201_CREATED, dependencies=[admin_protect])
async def create_grade(payload: GradeCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Grade).where((Grade.code == payload.code) | (Grade.name == payload.name)))
    if existing.scalar_one_or_none():
        raise AppBaseException("Grade definition with identical code or text identity space exists", 409)

    grade = Grade(**payload.model_dump())
    db.add(grade)
    await db.flush()
    return grade

@router.get("/grades", response_model=list[GradeOut])
async def list_grades(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Grade).order_by(Grade.name))
    return result.scalars().all()

@router.get("/grades/{slug}", response_model=GradeDetailOut)
async def get_grade_structure(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Grade).where(Grade.slug == slug))
    grade = result.scalar_one_or_none()
    if not grade:
        raise AppBaseException("Target grade record not found", 404)
    return grade

# --- SUBJECT ENDPOINTS ---
@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).order_by(Subject.name))
    return result.scalars().all()

@router.get("/subjects/{slug}", response_model=SubjectDetailOut)
async def get_subject_tree(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).where(Subject.slug == slug))
    subject = result.scalar_one_or_none()
    if not subject:
        raise AppBaseException("Subject record not found", 404)
    return subject


@router.get("/subjects/{subject_id}", response_model=SubjectDetailOut)
async def get_subject_tree(subject_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise AppBaseException("Subject record not found", 404)
    return subject

# --- TOPIC ENDPOINTS ---
@router.post("/subjects/{subject_id}/topics", response_model=TopicOut, status_code=status.HTTP_201_CREATED, dependencies=[educator_or_admin_protect])
async def create_topic(subject_id: UUID, payload: TopicCreate, db: AsyncSession = Depends(get_db)):
    sub_res = await db.execute(select(Subject).where(Subject.id == subject_id))
    if not sub_res.scalar_one_or_none():
        raise AppBaseException("Parent subject scope missing", 404)

    topic = Topic(subject_id=subject_id, **payload.model_dump())
    db.add(topic)
    await db.flush()
    return topic

# --- LEARNING OUTCOMES ---
@router.post("/topics/{topic_id}/outcomes", response_model=LearningOutcomeOut, status_code=status.HTTP_201_CREATED, dependencies=[educator_or_admin_protect])
async def add_learning_outcome(topic_id: UUID, payload: LearningOutcomeCreate, db: AsyncSession = Depends(get_db)):
    top_res = await db.execute(select(Topic).where(Topic.id == topic_id))
    if not top_res.scalar_one_or_none():
        raise AppBaseException("Parent topic scope missing", 404)

    outcome = LearningOutcome(topic_id=topic_id, **payload.model_dump())
    db.add(outcome)
    await db.flush()
    return outcome

# --- CURRICULUM RESOURCE ATTACHMENTS ---
@router.post("/topics/{topic_id}/resources", response_model=ResourceOut, status_code=status.HTTP_201_CREATED, dependencies=[educator_or_admin_protect])
async def add_curriculum_resource(topic_id: UUID, payload: ResourceCreate, db: AsyncSession = Depends(get_db)):
    top_res = await db.execute(select(Topic).where(Topic.id == topic_id))
    if not top_res.scalar_one_or_none():
        raise AppBaseException("Parent topic scope missing", 404)

    resource = CurriculumResource(topic_id=topic_id, **payload.model_dump())
    db.add(resource)
    await db.flush()
    return resource
