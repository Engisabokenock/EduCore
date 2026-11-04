import uuid
from typing import List
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.exceptions import AuthorizationError, AppBaseException
from app.core.security import safe_filename, validate_uploaded_file
from app.api.deps import get_current_active_user, PermissionGuard
from app.models.base import User, UserRole, DynamicPermission
from app.models.asset import PortalResource, WorkflowApprovalState
from app.models.notification import NotificationLog
from app.schemas.asset import ResourceUploadPayload, UnifiedResourceOut, ResourceModerationAction
from app.storage.r2 import StorageProvider

router = APIRouter(prefix="/internal-control-plane", tags=["Isolated Internal Management Control Plane"])

# Strict security boundaries: deny students and parents at the network edge
internal_staff_clearance = Depends(PermissionGuard(DynamicPermission.MANAGE_RESOURCES))
super_admin_clearance = Depends(PermissionGuard(DynamicPermission.MANAGE_SECURITY))


# --- 1. SECURE CONTENT INGESTION WORKSPACE (TEACHERS & ADMINS) ---

@router.post("/assets/ingest-binary", status_code=status.HTTP_201_CREATED, dependencies=[internal_staff_clearance])
async def internal_staff_upload_binary(
    file: UploadFile = File(...),
    storage: StorageProvider = Depends()
) -> dict:
    """
    Secure staff file ingestion pathway.

    Inspects file byte streams and MIME signatures before uploading to object storage.
    Returns the storage URL and detected extension for later metadata registration.
    """
    await validate_uploaded_file(file)
    bytes_data = await file.read()

    filename = safe_filename(file.filename, "upload.bin")
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"

    mime_map = {
        "pdf": "application/pdf",
        "csv": "text/csv",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "ppt": "application/vnd.ms-powerpoint",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "zip": "application/zip",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "mp4": "video/mp4",
        "mov": "video/quicktime",
    }
    content_type = mime_map.get(extension, "application/octet-stream")

    destination_key = f"internal_vault/{extension}s/{uuid.uuid4()}-{filename}"
    uploaded_url = await storage.upload_file(bytes_data, destination_key, content_type)
    return {"file_payload_url": uploaded_url, "extension": extension}


@router.post("/assets/register", response_model=UnifiedResourceOut, status_code=status.HTTP_201_CREATED)
async def internal_staff_register_metadata(
    payload: ResourceUploadPayload,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Registers uploaded content after file ingestion.

    Teachers -> Pending Review
    Admins / Super Admins -> Published
    """
    if current_user.role.name in [UserRole.STUDENT, UserRole.PARENT]:
        raise AuthorizationError("Access Denied: Public consumer profiles are blocked from internal ingestion planes.")

    intended_state = WorkflowApprovalState.PENDING_REVIEW
    if current_user.role.name in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        intended_state = WorkflowApprovalState.PUBLISHED

    resource = PortalResource(
        **payload.model_dump(),
        approval_state=intended_state,
        owner_id=current_user.id
    )
    db.add(resource)
    await db.flush()
    return resource


@router.get("/assets/teacher-workspace", response_model=List[UnifiedResourceOut], dependencies=[internal_staff_clearance])
async def get_teacher_submission_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Allows teachers to monitor their contributions and track review status.
    """
    stmt = select(PortalResource).where(PortalResource.owner_id == current_user.id).order_by(PortalResource.created_at.desc())
    ctx = await db.execute(stmt)
    return ctx.scalars().all()


# --- 2. THE CONTENT APPROVAL TRIAGE STREAM (ADMINS & SUPER ADMINS ONLY) ---

@router.get("/triage/pending-approvals", response_model=List[UnifiedResourceOut])
async def view_content_approval_queue(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a list of unapproved teacher uploads requiring quality review.
    """
    if current_user.role.name not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise AuthorizationError("Access Denied: Staging queue metrics are restricted to quality administrators.")

    stmt = select(PortalResource).where(PortalResource.approval_state == WorkflowApprovalState.PENDING_REVIEW).order_by(PortalResource.created_at.asc())
    ctx = await db.execute(stmt)
    return ctx.scalars().all()


@router.post("/triage/{asset_id}/moderate", response_model=UnifiedResourceOut)
async def moderate_incoming_resource(
    asset_id: uuid.UUID,
    payload: ResourceModerationAction,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Processes approval actions. Updates asset statuses to make approved resources
    available on public grids.
    """
    if current_user.role.name not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise AuthorizationError("Access Denied: Quality assurance actions require elevated administrator privileges.")

    stmt = select(PortalResource).where(PortalResource.id == asset_id)
    asset = (await db.execute(stmt)).scalar_one_or_none()
    if not asset:
        raise AppBaseException("Target curriculum resource missing", 404)

    if payload.target_state in (WorkflowApprovalState.DRAFT, WorkflowApprovalState.PENDING_REVIEW):
        raise AppBaseException("Moderation can only approve, reject or publish an asset.", 400)
    asset.approval_state = payload.target_state
    db.add(asset)
    await db.flush()
    return asset


# --- 3. IMMUTABLE SECURITY OPERATIONS GRID (SUPER ADMIN PLATFORM OWNER ONLY) ---

@router.get("/security/audit-trail", response_model=List[dict], dependencies=[super_admin_clearance])
async def fetch_platform_owner_security_logs(db: AsyncSession = Depends(get_db)):
    """
    Provides a clear list of network access trends, transaction logs, and platform
    activities for the Super Admin.
    """
    stmt = select(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(150)
    ctx = await db.execute(stmt)
    return [
        {
            "id": log.id,
            "event": log.event_type,
            "recipient": log.recipient_address,
            "timestamp": log.sent_at,
        }
        for log in ctx.scalars().all()
    ]
