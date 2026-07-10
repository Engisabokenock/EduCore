import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List, Optional
from app.core.database import get_db
from app.core.exceptions import AuthorizationError, AppBaseException
from app.api.deps import get_current_active_user
from app.models.base import User, UserRole
from app.models.asset import PortalResource, ExtendedResourceType, WorkflowApprovalState, AssetVisibilityScope
from app.models.subscription import UserSubscription, SubscriptionState
from app.models.payment import PaymentTransaction, TransactionStatus
from app.schemas.asset import UnifiedResourceOut

router = APIRouter(prefix="/portal-assets", tags=["Public Resource Discovery & Download Access"])


@router.get("", response_model=List[UnifiedResourceOut])
async def public_browse_resources(
    category: Optional[ExtendedResourceType] = Query(None),
    grade_id: Optional[uuid.UUID] = Query(None),
    subject_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Public discovery endpoint.

    Returns only published resources. Visibility filtering is applied here so the
    frontend never receives unpublished or private assets from public routes.
    """
    stmt = select(PortalResource).where(
        PortalResource.approval_state == WorkflowApprovalState.PUBLISHED
    )

    if category:
        stmt = stmt.where(PortalResource.category == category)
    if grade_id:
        stmt = stmt.where(PortalResource.grade_id == grade_id)
    if subject_id:
        stmt = stmt.where(PortalResource.subject_id == subject_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/download-gate/{asset_id}", status_code=status.HTTP_200_OK)
async def evaluate_download_clearance_vault(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The absolute source-of-truth download firewall.

    Checks:
    1. Resource existence
    2. Admin bypass
    3. Approval/publishing state
    4. Visibility scopes: private, school, registered, premium
    5. Subscription and single-item purchase receipts
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
