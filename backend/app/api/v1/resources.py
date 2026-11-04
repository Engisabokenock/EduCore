import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy import and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.deps import RoleChecker, get_optional_user
from app.core.cache import CacheManager
from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import safe_filename, validate_uploaded_file
from app.models.base import User, UserRole
from app.models.cbc import Grade, Subject, Topic
from app.models.resource import AcademicResource, AcademicTerm, ContentTag, ResourceTypeVariant
from app.schemas.resource import PaginatedResourceResponse, ResourceCreate, ResourceOut, ResourceStaffOut
from app.services import download_service
from app.storage.r2 import StorageProvider
from app.utils.text import slugify

router = APIRouter(prefix="/resources", tags=["Content Asset Management Engine"])

educator_or_admin_guard = Depends(RoleChecker([UserRole.ADMIN, UserRole.TEACHER]))
MAX_PAGE_SIZE = 100


def _with_relations(stmt):
    return stmt.options(
        selectinload(AcademicResource.grade),
        selectinload(AcademicResource.subject),
        selectinload(AcademicResource.topic),
        selectinload(AcademicResource.tags),
    )


@router.get("", response_model=PaginatedResourceResponse)
async def list_resources(
    db: AsyncSession = Depends(get_db),
    type: Optional[ResourceTypeVariant] = Query(None, description="Resource type filter"),
    grade_id: Optional[uuid.UUID] = None,
    subject_id: Optional[uuid.UUID] = None,
    topic_id: Optional[uuid.UUID] = None,
    grade: Optional[str] = Query(None, description="Grade slug (alternative to grade_id)"),
    subject: Optional[str] = Query(None, description="Subject slug (alternative to subject_id)"),
    topic: Optional[str] = Query(None, description="Topic slug (alternative to topic_id)"),
    term: Optional[AcademicTerm] = None,
    year: Optional[int] = None,
    is_premium: Optional[bool] = None,
    search: Optional[str] = Query(None, max_length=100),
    ordering: Optional[str] = Query(None, pattern=r"^-?(created_at|downloads_count|views_count|title)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
):
    """Public catalogue: only published, non-archived resources are ever returned."""
    conditions = [AcademicResource.is_archived.is_(False), AcademicResource.is_published.is_(True)]
    if type:
        conditions.append(AcademicResource.type_variant == type)
    if grade_id:
        conditions.append(AcademicResource.grade_id == grade_id)
    elif grade:
        conditions.append(AcademicResource.grade_id.in_(select(Grade.id).where(Grade.slug == grade)))
    if subject_id:
        conditions.append(AcademicResource.subject_id == subject_id)
    elif subject:
        conditions.append(AcademicResource.subject_id.in_(select(Subject.id).where(Subject.slug == subject)))
    if topic_id:
        conditions.append(AcademicResource.topic_id == topic_id)
    elif topic:
        conditions.append(AcademicResource.topic_id.in_(select(Topic.id).where(Topic.slug == topic)))
    if term is not None:
        conditions.append(AcademicResource.term == term)
    if year is not None:
        conditions.append(AcademicResource.year == year)
    if is_premium is not None:
        conditions.append(AcademicResource.is_premium.is_(is_premium))
    if search:
        conditions.append(func.lower(AcademicResource.title).contains(search.strip().lower(), autoescape=True))

    order_field = (ordering or "-created_at").lstrip("-")
    column = getattr(AcademicResource, order_field)
    order = desc(column) if (ordering or "-created_at").startswith("-") else column

    where = and_(*conditions)
    total = (await db.execute(select(func.count(AcademicResource.id)).where(where))).scalar() or 0
    stmt = _with_relations(select(AcademicResource).where(where)).order_by(order, AcademicResource.id)
    items = (await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    total_pages = max((total + page_size - 1) // page_size, 1)
    return {
        "count": total,
        "next": f"/resources?page={page + 1}" if page < total_pages else None,
        "previous": f"/resources?page={page - 1}" if page > 1 else None,
        "total_pages": total_pages,
        "current_page": page,
        "results": items,
    }


@router.get("/{slug}", response_model=ResourceOut)
async def get_resource_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Public resource detail (published resources only)."""
    resource = (await db.execute(
        _with_relations(select(AcademicResource)).where(
            AcademicResource.slug == slug,
            AcademicResource.is_published.is_(True),
            AcademicResource.is_archived.is_(False),
        )
    )).scalar_one_or_none()
    if not resource:
        raise NotFoundError("Resource not found.")
    return resource


@router.get("/{slug}/access")
async def check_resource_access(
    slug: str,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Tell the UI whether the current visitor may download this resource."""
    resource = await download_service.get_downloadable_resource(db, slug=slug)
    allowed = await download_service.can_access(db, resource, user)
    return {
        "can_access": allowed,
        "is_premium": resource.is_premium,
        "requires_login": resource.is_premium and user is None,
        "requires_subscription": resource.is_premium and user is not None and not allowed,
    }


@router.post("/{slug}/download", status_code=status.HTTP_200_OK)
async def request_download_by_slug(
    slug: str,
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Entitlement-checked download. Free resources work anonymously within the daily quota."""
    resource = await download_service.get_downloadable_resource(db, slug=slug)
    return await download_service.authorize_and_record(db, resource, user, request)


@router.post("/upload-pdf", status_code=status.HTTP_201_CREATED, dependencies=[educator_or_admin_guard])
async def upload_resource_pdf(file: UploadFile = File(...), storage: StorageProvider = Depends()) -> dict:
    """Upload a PDF (magic-byte verified) and return its stored URL for resource creation."""
    await validate_uploaded_file(file, allowed={"application/pdf"})
    data = await file.read()
    key = f"resources/pdfs/{uuid.uuid4()}-{safe_filename(file.filename, 'document.pdf')}"
    return {"pdf_url": await storage.upload_file(data, key, "application/pdf")}


async def _unique_slug(db: AsyncSession, base: str) -> str:
    slug, n = base, 2
    while (await db.execute(select(AcademicResource.id).where(AcademicResource.slug == slug))).scalar_one_or_none():
        slug = f"{base}-{n}"
        n += 1
    return slug


@router.post("", response_model=ResourceStaffOut, status_code=status.HTTP_201_CREATED)
async def create_resource(
    payload: ResourceCreate,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.TEACHER])),
    db: AsyncSession = Depends(get_db),
):
    """Create a resource. Published immediately unless scheduled for the future."""
    subject = (await db.execute(select(Subject).where(Subject.id == payload.subject_id))).scalar_one_or_none()
    if subject is None or subject.grade_id != payload.grade_id:
        raise NotFoundError("The selected subject does not belong to the selected grade.")
    if payload.topic_id:
        topic = (await db.execute(select(Topic).where(Topic.id == payload.topic_id))).scalar_one_or_none()
        if topic is None or topic.subject_id != payload.subject_id:
            raise NotFoundError("The selected topic does not belong to the selected subject.")

    if payload.slug:
        if (await db.execute(select(AcademicResource.id).where(AcademicResource.slug == payload.slug))).scalar_one_or_none():
            raise ConflictError("A resource with this slug already exists.")
        slug = payload.slug
    else:
        slug = await _unique_slug(db, slugify(payload.title, 200))

    now = datetime.now(timezone.utc)
    is_published = payload.scheduled_publish_at is None or payload.scheduled_publish_at <= now
    resource = AcademicResource(
        title=payload.title,
        description=payload.description,
        slug=slug,
        grade_id=payload.grade_id,
        subject_id=payload.subject_id,
        topic_id=payload.topic_id,
        term=payload.term,
        year=payload.year,
        pdf_url=payload.pdf_url,
        thumbnail_url=payload.thumbnail_url,
        type_variant=payload.type_variant,
        is_premium=payload.is_premium,
        is_published=is_published,
        scheduled_publish_at=payload.scheduled_publish_at,
        published_at=now if is_published else None,
        created_by_id=current_user.id,
    )

    tags: list[ContentTag] = []
    for name in {t.strip().lower()[:50] for t in payload.tags if t.strip()}:
        tag = (await db.execute(select(ContentTag).where(ContentTag.name == name))).scalar_one_or_none()
        if tag is None:
            tag = ContentTag(name=name)
            db.add(tag)
        tags.append(tag)
    resource.tags = tags

    db.add(resource)
    await db.flush()
    await CacheManager.invalidate_prefix("cache:search:")
    return (await db.execute(_with_relations(select(AcademicResource)).where(AcademicResource.id == resource.id))).scalar_one()


async def _get_for_staff(db: AsyncSession, resource_id: uuid.UUID) -> AcademicResource:
    resource = (await db.execute(
        _with_relations(select(AcademicResource)).where(AcademicResource.id == resource_id)
    )).scalar_one_or_none()
    if not resource:
        raise NotFoundError("Resource not found.")
    return resource


@router.post("/{resource_id}/publish", response_model=ResourceStaffOut, dependencies=[educator_or_admin_guard])
async def publish_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    resource = await _get_for_staff(db, resource_id)
    resource.is_published = True
    resource.is_archived = False
    resource.scheduled_publish_at = None
    resource.published_at = datetime.now(timezone.utc)
    await db.flush()
    await CacheManager.invalidate_prefix("cache:search:")
    return resource


@router.post("/{resource_id}/archive", response_model=ResourceStaffOut, dependencies=[educator_or_admin_guard])
async def archive_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    resource = await _get_for_staff(db, resource_id)
    resource.is_archived = True
    resource.is_published = False
    await db.flush()
    await CacheManager.invalidate_prefix("cache:search:")
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def purge_resource_permanently(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Hard-delete a resource (administrators only)."""
    resource = await _get_for_staff(db, resource_id)
    await db.delete(resource)
    await CacheManager.invalidate_prefix("cache:search:")
