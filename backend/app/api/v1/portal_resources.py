import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List
from app.core.database import get_db
from app.core.exceptions import AuthorizationError, AppBaseException
from app.api.deps import get_current_active_user, PermissionGuard
from app.models.base import User, UserRole, DynamicPermission
from app.models.asset import PortalResource, ExtendedResourceType, WorkflowApprovalState, AssetVisibilityScope
from app.models.subscription import UserSubscription, SubscriptionState
from app.models.payment import PaymentTransaction, TransactionStatus
from app.schemas.asset import ResourceUploadPayload, UnifiedResourceOut, MetadataUpdatePayload, ResourceModerationAction

router = APIRouter(prefix="/portal-assets", tags=["Absolute Resource Access Core Verification Engine"])


@router.post("", response_model=UnifiedResourceOut, status_code=status.HTTP_201_CREATED)
async def upload_educational_resource(
    payload: ResourceUploadPayload,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Enforces user capability matrix rules during file uploads.

    Restricts roles, determines draft states, and prevents unauthorized publication attempts.
    """
    if current_user.role.name in [UserRole.STUDENT, UserRole.PARENT]:
        raise AuthorizationError("Access Denied: Your account role is blocked from uploading resources")

    starting_state = WorkflowApprovalState.DRAFT
    if current_user.role.name in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        starting_state = WorkflowApprovalState.PUBLISHED

    resource = PortalResource(
        **payload.model_dump(),
        approval_state=starting_state,
        owner_id=current_user.id
    )
    db.add(resource)
    await db.flush()
    return resource


@router.get("/download-gate/{asset_id}", status_code=status.HTTP_200_OK)
async def evaluate_download_clearance_vault(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The Absolute Source of Truth Access Validator.

    Verifies object visibility, cross-checks active subscription balances,
    and checks single-item receipt states. Returns a 403 Forbidden error if checks fail.
    """
    stmt = select(PortalResource).where(PortalResource.id == asset_id)
    asset = (await db.execute(stmt)).scalar_one_or_none()

    if not asset:
        raise AppBaseException("Resource not found", 404)

    if current_user.role.name in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        return {"clearance": "granted", "download_url": asset.file_url}

    if asset.approval_state != WorkflowApprovalState.PUBLISHED:
        if asset.owner_id != current_user.id:
            raise AuthorizationError("403 Forbidden: Content is undergoing administrative quality review cascades")

    if asset.visibility == AssetVisibilityScope.PRIVATE:
        if asset.owner_id != current_user.id:
            raise AuthorizationError("403 Forbidden: Resource access is restricted to the content owner")

    if asset.visibility == AssetVisibilityScope.SCHOOL:
        if not hasattr(current_user, "school_id") or current_user.school_id != asset.school_id:
             raise AuthorizationError("403 Forbidden: Resource access is restricted to members of the specific school")

    if asset.visibility == AssetVisibilityScope.PREMIUM or not asset.is_free:
        if asset.requires_subscription:
            sub_stmt = select(UserSubscription).where(
                and_(UserSubscription.user_id == current_user.id, UserSubscription.status == SubscriptionState.ACTIVE)
            )
            if (await db.execute(sub_stmt)).scalar_one_or_none():
                return {"clearance": "granted", "download_url": asset.file_url}

        payment_stmt = select(PaymentTransaction).where(
            and_(
                PaymentTransaction.user_id == current_user.id,
                PaymentTransaction.status == TransactionStatus.COMPLETED,
                PaymentTransaction.merchant_request_id == f"PAY-{asset.id.hex[:12].upper()}"
            )
        )
        if (await db.execute(payment_stmt)).scalar_one_or_none():
             return {"clearance": "granted", "download_url": asset.file_url}

        raise AuthorizationError("403 Forbidden: Access Denied. Requires an active subscription package or a direct item purchase.")

    return {"clearance": "granted", "download_url": asset.file_url}


@router.post("/moderation/{asset_id}/action", response_model=UnifiedResourceOut, dependencies=[Depends(PermissionGuard(DynamicPermission.MANAGE_SETTINGS))])
async def manage_resource_workflow_state(
    asset_id: uuid.UUID,
    payload: ResourceModerationAction,
    db: AsyncSession = Depends(get_db)
):
    """Allows administrators to approve, reject, or publish submitted teacher resources."""
    stmt = select(PortalResource).where(PortalResource.id == asset_id)
    asset = (await db.execute(stmt)).scalar_one_or_none()

    if not asset:
        raise AppBaseException("Target content asset records reference missing", 404)

    asset.approval_state = payload.target_state
    db.add(asset)
    return asset


@router.patch("/{asset_id}/metadata", response_model=UnifiedResourceOut)
async def update_resource_metadata(
    asset_id: uuid.UUID,
    payload: MetadataUpdatePayload,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Enables self-service metadata corrections for teachers on drafts, or full modifications for admins."""
    stmt = select(PortalResource).where(PortalResource.id == asset_id)
    asset = (await db.execute(stmt)).scalar_one_or_none()

    if not asset:
         raise AppBaseException("Resource missing", 404)

    if asset.owner_id != current_user.id and current_user.role.name not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise AuthorizationError("Access Denied: Insufficient metadata modification privileges")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)

    if current_user.role.name == UserRole.TEACHER:
        asset.approval_state = WorkflowApprovalState.PENDING_REVIEW

    db.add(asset)
    return asset
