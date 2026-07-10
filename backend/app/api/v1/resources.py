import uuid
import secrets
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.exceptions import AppBaseException, AuthorizationError
from app.api.deps import get_current_user, RoleChecker
from app.models.base import User, UserRole
from app.models.resource import AcademicResource, ContentTag, ResourceTypeVariant, AcademicTerm
from app.models.tracking import DownloadLog
from app.schemas.resource import ResourceCreate, ResourceOut, PaginatedResourceResponse
from app.storage.r2 import StorageProvider

router = APIRouter(prefix="/resources", tags=["Content Asset Management Engine"])

# Content Operations Authorization Rules
educator_or_admin_guard = Depends(RoleChecker([UserRole.ADMIN, UserRole.TEACHER]))


@router.get("", response_model=PaginatedResourceResponse)
async def list_resources(
    db: AsyncSession = Depends(get_db),
    type: Optional[str] = Query(None),
    grade_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    term: Optional[AcademicTerm] = None,
    year: Optional[int] = None,
    is_published: bool = True,
    ordering: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    conditions = [
        AcademicResource.is_archived == False,
        AcademicResource.is_published == is_published,
    ]
    if type:
        try:
            conditions.append(AcademicResource.type_variant == ResourceTypeVariant(type))
        except ValueError:
            raise AppBaseException("Invalid resource type", 400)
    if grade_id:
        conditions.append(AcademicResource.grade_id == grade_id)
    if subject_id:
        conditions.append(AcademicResource.subject_id == subject_id)
    if topic_id:
        conditions.append(AcademicResource.topic_id == topic_id)
    if term is not None:
        conditions.append(AcademicResource.term == term)
    if year is not None:
        conditions.append(AcademicResource.year == year)

    base_stmt = select(AcademicResource).options(
        selectinload(AcademicResource.grade),
        selectinload(AcademicResource.subject),
        selectinload(AcademicResource.topic),
    ).where(and_(*conditions))

    if ordering == "-downloads_count":
        base_stmt = base_stmt.order_by(desc(AcademicResource.downloads_count))
    elif ordering == "-views_count":
        base_stmt = base_stmt.order_by(desc(AcademicResource.views_count))
    elif ordering == "-created_at":
        base_stmt = base_stmt.order_by(desc(AcademicResource.created_at))
    else:
        base_stmt = base_stmt.order_by(desc(AcademicResource.created_at))

    total = (await db.execute(select(func.count(AcademicResource.id)).where(and_(*conditions)))).scalar() or 0

    offset = (page - 1) * page_size
    stmt = base_stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    total_pages = max((total + page_size - 1) // page_size, 1)
    base_url = f"/resources"
    return {
        "count": total,
        "next": f"{base_url}?page={page + 1}" if page < total_pages else None,
        "previous": f"{base_url}?page={page - 1}" if page > 1 else None,
        "total_pages": total_pages,
        "current_page": page,
        "results": items,
    }




@router.get("/{slug}", response_model=ResourceOut)
async def get_resource_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint: get a single resource by slug."""
    result = await db.execute(
        select(AcademicResource)
        .options(
            selectinload(AcademicResource.grade),
            selectinload(AcademicResource.subject),
            selectinload(AcademicResource.topic),
        )
        .where(AcademicResource.slug == slug)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise AppBaseException("Resource record not found", 404)
    return resource


@router.post("/{slug}/download", status_code=status.HTTP_200_OK)
async def request_download_by_slug(
    slug: str,
    request: Request,
    user_context: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Public download request by slug.

    Returns a clearance token and the PDF URL for the frontend to use.
    Premium access checks are enforced.
    """
    res = await db.execute(select(AcademicResource).where(AcademicResource.slug == slug))
    resource = res.scalar_one_or_none()
    if not resource or resource.is_archived:
        raise AppBaseException("Resource record not found", 404)

    if resource.is_premium:
        if not user_context:
            raise AuthorizationError("Premium content requires authentication")
        if user_context.role.name not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise AuthorizationError("Active subscription required for premium content")

    ip_addr = request.client.host if request.client else "0.0.0.0"
    user_agent = request.headers.get("user-agent", "Unknown")
    country_code = request.headers.get("cf-ipcountry", "KE")[:3].upper()

    db.add(
        DownloadLog(
            resource_id=resource.id,
            user_id=user_context.id if user_context else None,
            ip_address=ip_addr,
            device_fingerprint=user_agent[:512],
            country_code=country_code,
        )
    )
    resource.downloads_count += 1
    db.add(resource)
    await db.flush()

    return {
        "url": resource.pdf_url,
        "download_clearance_token": secrets.token_urlsafe(32),
    }


@router.post("/upload-pdf", status_code=status.HTTP_201_CREATED, dependencies=[educator_or_admin_guard])
async def upload_resource_pdf(file: UploadFile = File(...), storage: StorageProvider = Depends()) -> dict:
    """Streams asset drops to isolated Cloudflare object containers securely."""
    if file.content_type != "application/pdf":
        raise AppBaseException("Validation constraints broken: Upload asset must target PDF types", 400)

    bytes_data = await file.read()
    destination_key = f"resources/pdfs/{uuid.uuid4()}-{file.filename}"
    url = await storage.upload_file(bytes_data, destination_key, "application/pdf")
    return {"pdf_url": url}


@router.post("", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def create_resource(
    payload: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new resource.

    Authorization: only ADMIN or TEACHER roles can create resources.
    Auto-publishes if scheduled_publish_at is in the past or not set.
    """
    if current_user.role.name not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise AuthorizationError("Identity policies block asset ingestion pathways")

    now = datetime.now(timezone.utc)
    if payload.scheduled_publish_at is None or payload.scheduled_publish_at <= now:
        is_published = True  # Immediate operational deployment vector
    else:
        is_published = False  # Held until scheduled_publish_at

    resource = AcademicResource(
        title=payload.title,
        description=payload.description,
        slug=payload.slug,
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
        published_at=datetime.now(timezone.utc) if is_published else None,
        created_by_id=current_user.id,
    )

    # Resolve tag associations (get-or-create)
    tag_objs: list[ContentTag] = []
    for name in payload.tags:
        result = await db.execute(select(ContentTag).where(ContentTag.name == name))
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = ContentTag(name=name)
            db.add(tag)
            await db.flush()
        tag_objs.append(tag)
    resource.tags = tag_objs

    db.add(resource)
    await db.flush()
    return resource


@router.post("/{resource_id}/publish", response_model=ResourceOut, dependencies=[educator_or_admin_guard])
async def publish_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Publish a draft or scheduled resource immediately."""
    res_stmt = await db.execute(select(AcademicResource).where(AcademicResource.id == resource_id))
    resource = res_stmt.scalar_one_or_none()
    if not resource:
         raise AppBaseException("Target resource reference does not exist", 404)

    resource.is_published = True
    resource.scheduled_publish_at = None
    resource.published_at = datetime.now(timezone.utc)
    db.add(resource)
    return resource


@router.post("/{resource_id}/archive", response_model=ResourceOut, dependencies=[educator_or_admin_guard])
async def archive_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Archive a resource so it no longer appears in public listings."""
    res_stmt = await db.execute(select(AcademicResource).where(AcademicResource.id == resource_id))
    resource = res_stmt.scalar_one_or_none()
    if not resource:
         raise AppBaseException("Resource record not found", 404)

    resource.is_archived = True
    resource.is_published = False
    db.add(resource)
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def purge_resource_permanently(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Hard-purge a resource from the database entirely. Restricted to Administrators."""
    res_stmt = await db.execute(select(AcademicResource).where(AcademicResource.id == resource_id))
    resource = res_stmt.scalar_one_or_none()
    if not resource:
         raise AppBaseException("Resource record not found", 404)
    await db.delete(resource)

