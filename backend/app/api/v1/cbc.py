from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import raiseload, selectinload

from app.api.deps import RoleChecker
from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.models.base import UserRole
from app.models.cbc import CurriculumResource, Grade, LearningOutcome, Subject, Topic
from app.models.resource import AcademicResource
from app.schemas.cbc import (
    GradeCreate, GradeDetailOut, GradeOut,
    LearningOutcomeCreate, LearningOutcomeOut,
    ResourceCreate, ResourceOut,
    SubjectCreate, SubjectDetailOut, SubjectOut,
    TopicCreate, TopicOut,
)
from app.utils.text import slugify

router = APIRouter(prefix="/academic", tags=["CBC Curriculum Management Vector"])

admin_protect = Depends(RoleChecker([UserRole.ADMIN]))
educator_or_admin_protect = Depends(RoleChecker([UserRole.ADMIN, UserRole.TEACHER]))


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _subject_topic_counts(db: AsyncSession, subject_ids: list) -> dict:
    if not subject_ids:
        return {}
    rows = await db.execute(
        select(Topic.subject_id, func.count(Topic.id))
        .where(Topic.subject_id.in_(subject_ids), Topic.is_active.is_(True))
        .group_by(Topic.subject_id)
    )
    return dict(rows.all())


async def _attach_topic_resource_counts(db: AsyncSession, topics: list[Topic]) -> None:
    """Count curriculum attachments plus published catalogue resources per topic."""
    if not topics:
        return
    ids = [t.id for t in topics]
    attachments = dict((await db.execute(
        select(CurriculumResource.topic_id, func.count()).where(CurriculumResource.topic_id.in_(ids))
        .group_by(CurriculumResource.topic_id)
    )).all())
    catalogue = dict((await db.execute(
        select(AcademicResource.topic_id, func.count())
        .where(AcademicResource.topic_id.in_(ids), AcademicResource.is_published.is_(True),
               AcademicResource.is_archived.is_(False))
        .group_by(AcademicResource.topic_id)
    )).all())
    for topic in topics:
        topic.resource_count = attachments.get(topic.id, 0) + catalogue.get(topic.id, 0)


async def _find_subject(db: AsyncSession, slug: str, grade: Optional[str], with_topics: bool) -> Subject:
    """
    Subject slugs repeat across grades ("mathematics" exists in every grade), so the
    lookup is scoped by grade slug when given and otherwise picks the lowest grade.
    """
    stmt = (
        select(Subject)
        .join(Grade, Subject.grade_id == Grade.id)
        .where(Subject.slug == slug, Subject.is_active.is_(True))
        .options(selectinload(Subject.grade).raiseload(Grade.subjects))
        .order_by(Grade.order, Grade.name)
        .limit(1)
    )
    if grade:
        stmt = stmt.where(Grade.slug == grade)
    stmt = stmt.options(selectinload(Subject.topics) if with_topics else raiseload(Subject.topics))
    subject = (await db.execute(stmt)).scalars().first()
    if subject is None:
        raise NotFoundError("Subject not found.")
    return subject


# ── Grades ───────────────────────────────────────────────────────────────────

@router.post("/grades", response_model=GradeOut, status_code=status.HTTP_201_CREATED, dependencies=[admin_protect])
async def create_grade(payload: GradeCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump()
    data["slug"] = data.get("slug") or slugify(payload.name, 50)
    existing = await db.execute(
        select(Grade.id).where((Grade.code == payload.code) | (Grade.name == payload.name) | (Grade.slug == data["slug"]))
    )
    if existing.first():
        raise ConflictError("A grade with this name, code or slug already exists.")
    grade = Grade(**data)
    db.add(grade)
    await db.flush()
    return GradeOut.model_validate(grade, from_attributes=True)


@router.get("/grades", response_model=list[GradeOut])
async def list_grades(curriculum: Optional[str] = Query(None, max_length=20), db: AsyncSession = Depends(get_db)):
    """Active grades in curriculum order, with subject counts (subjects themselves are not embedded)."""
    stmt = select(Grade).options(raiseload(Grade.subjects)).where(Grade.is_active.is_(True)).order_by(Grade.order, Grade.name)
    if curriculum:
        stmt = stmt.where(Grade.curriculum == curriculum.upper())
    grades = (await db.execute(stmt)).scalars().all()
    counts = dict((await db.execute(
        select(Subject.grade_id, func.count(Subject.id)).where(Subject.is_active.is_(True)).group_by(Subject.grade_id)
    )).all())
    for grade in grades:
        grade.subject_count = counts.get(grade.id, 0)
    return grades


@router.get("/grades/{slug}", response_model=GradeDetailOut)
async def get_grade_structure(slug: str, db: AsyncSession = Depends(get_db)):
    """A grade with its subjects (and each subject's topic count)."""
    grade = (await db.execute(
        select(Grade).where(Grade.slug == slug)
        .options(selectinload(Grade.subjects).raiseload(Subject.topics))
    )).scalar_one_or_none()
    if not grade:
        raise NotFoundError("Grade not found.")
    subjects = [s for s in grade.subjects if s.is_active]
    counts = await _subject_topic_counts(db, [s.id for s in subjects])
    grade_info = {"id": grade.id, "name": grade.name, "slug": grade.slug, "code": grade.code}
    # Build the response explicitly: reassigning grade.subjects would mark inactive
    # subjects as orphans and delete them on commit.
    return {
        "id": grade.id,
        "name": grade.name,
        "code": grade.code,
        "description": grade.description,
        "slug": grade.slug,
        "curriculum": grade.curriculum,
        "is_active": grade.is_active,
        "order": grade.order,
        "subject_count": len(subjects),
        "subjects": [
            {
                "id": s.id, "name": s.name, "code": s.code, "description": s.description,
                "slug": s.slug, "icon": s.icon, "color": s.color, "is_active": s.is_active,
                "order": s.order, "topic_count": counts.get(s.id, 0), "grade": grade_info,
            }
            for s in subjects
        ],
    }


# ── Subjects ─────────────────────────────────────────────────────────────────

@router.post("/grades/{grade_id}/subjects", response_model=SubjectDetailOut, status_code=status.HTTP_201_CREATED,
             dependencies=[admin_protect])
async def create_subject(grade_id: UUID, payload: SubjectCreate, db: AsyncSession = Depends(get_db)):
    grade = (await db.execute(select(Grade).where(Grade.id == grade_id))).scalar_one_or_none()
    if not grade:
        raise NotFoundError("Grade not found.")
    data = payload.model_dump()
    data["slug"] = data.get("slug") or slugify(payload.name, 100)
    if (await db.execute(select(Subject.id).where(Subject.code == payload.code))).first():
        raise ConflictError("A subject with this code already exists.")
    if (await db.execute(select(Subject.id).where(Subject.grade_id == grade_id, Subject.slug == data["slug"]))).first():
        raise ConflictError("This grade already has a subject with that slug.")
    subject = Subject(grade_id=grade_id, **data)
    subject.grade = grade
    subject.topics = []
    db.add(subject)
    await db.flush()
    return subject


@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(
    grade: Optional[str] = Query(None, description="Restrict to one grade (slug)"),
    db: AsyncSession = Depends(get_db),
):
    """Active subjects with their grade and topic count (topics are not embedded)."""
    stmt = (
        select(Subject)
        .join(Grade, Subject.grade_id == Grade.id)
        .where(Subject.is_active.is_(True))
        .options(selectinload(Subject.grade).raiseload(Grade.subjects), raiseload(Subject.topics))
        .order_by(Grade.order, Subject.order, Subject.name)
    )
    if grade:
        stmt = stmt.where(Grade.slug == grade)
    subjects = (await db.execute(stmt)).scalars().all()
    counts = await _subject_topic_counts(db, [s.id for s in subjects])
    for subject in subjects:
        subject.topic_count = counts.get(subject.id, 0)
    return subjects


@router.get("/subjects/{slug}", response_model=SubjectDetailOut)
async def get_subject_tree(
    slug: str,
    grade: Optional[str] = Query(None, description="Grade slug; required to disambiguate shared subject slugs"),
    db: AsyncSession = Depends(get_db),
):
    subject = await _find_subject(db, slug, grade, with_topics=True)
    topics = [t for t in subject.topics if t.is_active]
    await _attach_topic_resource_counts(db, topics)
    subject.topic_count = len(topics)
    data = SubjectOut.model_validate(subject).model_dump()
    data["topics"] = [TopicOut.model_validate(t).model_dump() for t in topics]
    return data


@router.get("/subjects/{slug}/topics", response_model=list[TopicOut])
async def list_subject_topics(
    slug: str,
    grade: Optional[str] = Query(None, description="Grade slug"),
    db: AsyncSession = Depends(get_db),
):
    subject = await _find_subject(db, slug, grade, with_topics=True)
    topics = [t for t in subject.topics if t.is_active]
    await _attach_topic_resource_counts(db, topics)
    return topics


# ── Topics, outcomes and attachments ─────────────────────────────────────────

@router.post("/subjects/{subject_id}/topics", response_model=TopicOut, status_code=status.HTTP_201_CREATED,
             dependencies=[educator_or_admin_protect])
async def create_topic(subject_id: UUID, payload: TopicCreate, db: AsyncSession = Depends(get_db)):
    if not (await db.execute(select(Subject.id).where(Subject.id == subject_id))).first():
        raise NotFoundError("Subject not found.")
    data = payload.model_dump()
    data["slug"] = data.get("slug") or slugify(payload.name, 150)
    if (await db.execute(select(Topic.id).where(Topic.subject_id == subject_id, Topic.slug == data["slug"]))).first():
        raise ConflictError("This subject already has a topic with that slug.")
    topic = Topic(subject_id=subject_id, **data)
    topic.learning_outcomes = []
    db.add(topic)
    await db.flush()
    return topic


@router.post("/topics/{topic_id}/outcomes", response_model=LearningOutcomeOut, status_code=status.HTTP_201_CREATED,
             dependencies=[educator_or_admin_protect])
async def add_learning_outcome(topic_id: UUID, payload: LearningOutcomeCreate, db: AsyncSession = Depends(get_db)):
    if not (await db.execute(select(Topic.id).where(Topic.id == topic_id))).first():
        raise NotFoundError("Topic not found.")
    if payload.code and (await db.execute(select(LearningOutcome.id).where(LearningOutcome.code == payload.code))).first():
        raise ConflictError("A learning outcome with this code already exists.")
    outcome = LearningOutcome(topic_id=topic_id, **payload.model_dump())
    db.add(outcome)
    await db.flush()
    return outcome


@router.post("/topics/{topic_id}/resources", response_model=ResourceOut, status_code=status.HTTP_201_CREATED,
             dependencies=[educator_or_admin_protect])
async def add_curriculum_resource(topic_id: UUID, payload: ResourceCreate, db: AsyncSession = Depends(get_db)):
    if not (await db.execute(select(Topic.id).where(Topic.id == topic_id))).first():
        raise NotFoundError("Topic not found.")
    resource = CurriculumResource(topic_id=topic_id, **payload.model_dump())
    db.add(resource)
    await db.flush()
    return resource
