import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from typing import Optional
from app.core.database import get_db
from app.core.exceptions import AppBaseException, AuthorizationError
from app.api.deps import get_current_user, RoleChecker
from app.models.base import User, UserRole
from app.models.resource import AcademicResource, ContentTag, ResourceTypeVariant, AcademicTerm
from app.schemas.resource import ResourceCreate, ResourceUpdate, ResourceOut
from app.storage.r2 import StorageProvider

router = APIRouter(prefix="/resources", tags=["Content Asset Management Engine"])

# Content Operations Authorization Rules
educator_or_admin_guard = Depends(RoleChecker([UserRole.ADMIN, UserRole.TEACHER]))

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
    if current_user.role.name not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise AuthorizationError("Identity policies block asset ingestion pathways")

    # Automated processing initialization block
    now = datetime.now(timezone.utc)
    if payload.scheduled_publish_at is None or payload.scheduled_publish_at <= now:
        is_published = True  # Immediate operational deployment vector
    else:
        is_published = False  # Held until scheduled_publish_at

    resource = AcademicResource(
        title=payload.title,
        description=payload.description,
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
    res_stmt = await db.execute(select(AcademicResource).where(AcademicResource.id == resource_id))
    resource = res_stmt.scalar_one_or_none()
    if not resource:
         raise AppBaseException("Target resource reference does not exist", 404)

    resource.is_published = True
    resource.scheduled_publish_at = None
    db.add(resource)
    return resource

@router.post("/{resource_id}/archive", response_model=ResourceOut, dependencies=[educator_or_admin_guard])
async def archive_resource(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    res_stmt = await db.execute(select(AcademicResource).where(AcademicResource.id == resource_id))
    resource = res_stmt.scalar_one_or_none()
    if not resource:
         raise AppBaseException("Target resource reference does not exist", 404)

    resource.is_archived = True
    resource.is_published = False
    db.add(resource)
    return resource

@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def purge_resource_permanently(resource_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Hard-purges targeted records from database tables entirely (Restricted to Administrators)."""
    res_stmt = await db.execute(select(AcademicResource).where(AcademicResource.id == resource_id))
    resource = res_stmt.scalar_one_or_none()
    if not resource:
         raise AppBaseException("Resource record not found", 404)
    await db.delete(resource)
