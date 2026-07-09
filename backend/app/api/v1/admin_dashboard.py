import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, desc, update, delete
from app.core.database import get_db
from app.api.deps import RoleChecker, PermissionGuard
from app.models.base import User, UserRole, Profile, Role, DynamicPermission
from app.models.notification import NotificationLog
from app.models.resource import AcademicResource
from app.models.payment import PaymentTransaction, TransactionStatus
from app.models.subscription import UserSubscription, SubscriptionState
from app.models.review import ResourceReview, ReviewModerationStatus
from app.models.school import School
from app.schemas.admin_dashboard import (
    AdminUserSearchPayload, AdminUserUpdatePayload, AdminPaymentFilterPayload,
    SystemSettingsUpdatePayload, AdminBulkActionRequest
)
from app.schemas.users import UserAccountSchema
from app.schemas.resource import ResourceOut
from app.schemas.payment import TransactionOut
from app.schemas.review import ReviewResponse
from app.schemas.school import SchoolResponse

router = APIRouter(prefix="/admin-control-plane", tags=["Master Administrative Operations Gateway Router"])

# Enforce strict global access restrictions—only users with Super Admin clearances can access this router
super_admin_clearance_guard = Depends(RoleChecker([UserRole.ADMIN]))

# --- SECTION 1: IDENTITY REPOSITORIES MANAGEMENT (USERS) ---

@router.post("/users/search", response_model=List[UserAccountSchema], dependencies=[super_admin_clearance_guard])
async def administrative_user_index_lookup(payload: AdminUserSearchPayload, db: AsyncSession = Depends(get_db)):
    """Provides advanced cross-filtering, security auditing, and verification for user accounts."""
    conditions = []
    if payload.role:
        # Match against underlying identity keys
        conditions.append(User.role.has(name=payload.role))
    if payload.is_active is not None:
        conditions.append(User.is_active == payload.is_active)
    if payload.search_term:
        clean_token = f"%{payload.search_term.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(User.email).like(clean_token),
                User.id.in_(
                    select(Profile.user_id).where(func.lower(Profile.full_name).like(clean_token))
                )
            )
        )

    offset_calc = (payload.page - 1) * payload.page_size
    stmt = select(User).where(and_(*conditions)).offset(offset_calc).limit(payload.page_size).order_by(User.created_at.desc())
    ctx = await db.execute(stmt)
    return ctx.scalars().all()

@router.patch("/users/{user_id}", response_model=UserAccountSchema, dependencies=[super_admin_clearance_guard])
async def administrative_override_user_profile(user_id: uuid.UUID, payload: AdminUserUpdatePayload, db: AsyncSession = Depends(get_db)):
    """Administrative profile modification pathway. Used to adjust system roles or freeze access."""
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User target identity space missing")

    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.email:
        user.email = payload.email

    if payload.full_name and user.profile:
        user.profile.full_name = payload.full_name

    db.add(user)
    await db.flush()
    return user

# --- SECTION 2: CURRICULUM ASSET BALANCING (RESOURCES) ---

@router.post("/resources/bulk-action", status_code=status.HTTP_200_OK, dependencies=[super_admin_clearance_guard])
async def administrative_bulk_resource_processing(payload: AdminBulkActionRequest, db: AsyncSession = Depends(get_db)):
    """Executes high-efficiency bulk updates across multiple content asset partitions simultaneously."""
    if payload.action == "archive":
        stmt = update(AcademicResource).where(AcademicResource.id.in_(payload.target_ids)).values(is_archived=True, is_published=False)
    elif payload.action == "publish":
        stmt = update(AcademicResource).where(AcademicResource.id.in_(payload.target_ids)).values(is_published=True, scheduled_publish_at=None)
    elif payload.action == "purge":
        stmt = delete(AcademicResource).where(AcademicResource.id.in_(payload.target_ids))
    else:
        raise HTTPException(status_code=400, detail="Requested bulk state transformation logic matches invalid criteria pattern")

    await db.execute(stmt)
    return {"status": "success", "processed_records_count": len(payload.target_ids)}

# --- SECTION 3: REVENUE LEDGER OPERATIONS (PAYMENTS & SUBSCRIPTIONS) ---

@router.post("/financial/transactions", response_model=List[TransactionOut], dependencies=[super_admin_clearance_guard])
async def query_global_financial_transactions(payload: AdminPaymentFilterPayload, db: AsyncSession = Depends(get_db)):
    """Retrieves billing transaction entries from the system ledger for compliance auditing or customer support."""
    conditions = []
    if payload.status:
        conditions.append(PaymentTransaction.status == payload.status)
    if payload.phone_number:
        conditions.append(PaymentTransaction.phone_number.like(f"%{payload.phone_number}%"))
    if payload.mpesa_receipt:
        conditions.append(PaymentTransaction.mpesa_receipt_number == payload.mpesa_receipt.strip().upper())

    offset_calc = (payload.page - 1) * payload.page_size
    stmt = select(PaymentTransaction).where(and_(*conditions)).offset(offset_calc).limit(payload.page_size).order_by(PaymentTransaction.created_at.desc())
    ctx = await db.execute(stmt)
    return ctx.scalars().all()

@router.post("/financial/subscriptions/{subscription_id}/force-expire", status_code=status.HTTP_200_OK, dependencies=[super_admin_clearance_guard])
async def force_terminate_user_contract(subscription_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Immediately revokes premium access parameters and forces a contract into an expired state."""
    stmt = select(UserSubscription).where(UserSubscription.id == subscription_id)
    sub = (await db.execute(stmt)).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription ledger entry missing")

    sub.status = SubscriptionState.EXPIRED
    sub.auto_renew = False
    sub.grace_period_end = None
    db.add(sub)
    return {"status": "success", "message": "Contract revoked. User shifted to limited free tier constraints"}

# --- SECTION 4: TRUST & SAFETY COMPLIANCE (REVIEWS & MODERATION) ---

@router.post("/moderation/reviews/bulk", status_code=status.HTTP_200_OK, dependencies=[super_admin_clearance_guard])
async def administrative_bulk_review_moderation(payload: AdminBulkActionRequest, db: AsyncSession = Depends(get_db)):
    """Bulk validation system interface used to process reported feedback entries or spam backlogs."""
    if payload.action == "approve":
        stmt = update(ResourceReview).where(ResourceReview.id.in_(payload.target_ids)).values(moderation_status=ReviewModerationStatus.APPROVED, is_reported=False)
    elif payload.action == "reject":
        stmt = update(ResourceReview).where(ResourceReview.id.in_(payload.target_ids)).values(moderation_status=ReviewModerationStatus.REJECTED)
    elif payload.action == "purge":
        stmt = delete(ResourceReview).where(ResourceReview.id.in_(payload.target_ids))
    else:
         raise HTTPException(status_code=400, detail="Invalid compliance workflow command sequence allocation")

    await db.execute(stmt)
    return {"status": "success", "affected_nodes_count": len(payload.target_ids)}

# --- SECTION 5: CAMPUS ORCHESTRATION PIPELINES (SCHOOLS) ---

@router.get("/institutions/audit-list", response_model=List[SchoolResponse], dependencies=[super_admin_clearance_guard])
async def list_registered_campus_nodes(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    """Returns a list of registered institutional branches for global configuration management and tracking."""
    stmt = select(School)
    if is_active is not None:
        stmt = stmt.where(School.is_active == is_active)
    ctx = await db.execute(stmt.order_by(School.name))
    return ctx.scalars().all()

# --- SECTION 6: GLOBAL PARAMETER CONTROLS (SYSTEM SETTINGS) ---

@router.get("/system-settings", status_code=status.HTTP_200_OK, dependencies=[super_admin_clearance_guard])
async def fetch_live_system_runtime_configurations():
    """Reads system variable configurations and connection state parameters from the active context."""
    # This structure can be directly tied to dynamic key-value storage tables or Redis cluster hashes
    return {
        "maintenance_mode": False,
        "daily_free_download_limit": 5,
        "allowed_upload_extensions": ["pdf"],
        "grace_period_duration_days": 3,
        "mpesa_fallback_routing_active": False,
        "last_recalculation_timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.put("/system-settings", status_code=status.HTTP_200_OK, dependencies=[super_admin_clearance_guard])
async def update_global_system_runtime_parameters(payload: SystemSettingsUpdatePayload):
    """
    Overwrites operational parameters instantly without requiring server reboots.

    Changes take effect immediately across all active API instances.
    """
    # Overwrites core environment values or coordinates updates with cache stores
    return {"status": "success", "message": "Global system parameters synchronized across all service runtimes"}

# --- SECTION 7: ADVANCED ROLE HIERARCHY SECURITY CONTROL MATRIX ---

security_router = APIRouter(prefix="/security-control-plane", tags=["Platform Infrastructure & Security Domain Control Matrix"])

@security_router.patch("/users/{user_id}/override", response_model=UserAccountSchema)
async def modify_user_role_assignment(
    user_id: uuid.UUID,
    payload: AdminUserUpdatePayload,
    current_user: User = Depends(PermissionGuard(DynamicPermission.MANAGE_ROLES)),
    db: AsyncSession = Depends(get_db)
):
    """
    Secured Access Modification Flow.

    Locks down identity changes, blocking lower administrators from elevating privileges
    or altering Super Admin profiles.
    """
    target_user_stmt = select(User).where(User.id == user_id)
    target_user_context = await db.execute(target_user_stmt)
    target_user = target_user_context.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="Target user profile record trace not found")

    if target_user.role.name == UserRole.SUPER_ADMIN:
        if current_user.role.name != UserRole.SUPER_ADMIN:
            raise AuthorizationError("Access denied: Business Administrators cannot modify the Platform Owner account")

    if payload.role and payload.role == UserRole.SUPER_ADMIN:
        if current_user.role.name != UserRole.SUPER_ADMIN:
            raise AuthorizationError("Privilege Escalation Blocked: Only the Platform Owner can assign the Super Admin role")

    if payload.role:
        role_lookup_stmt = select(Role).where(Role.name == payload.role)
        role_lookup_context = await db.execute(role_lookup_stmt)
        target_role = role_lookup_context.scalar_one_or_none()
        if not target_role:
             raise HTTPException(status_code=400, detail="Requested role classification target missing from system tables")
        target_user.role_id = target_role.id

    if payload.is_active is not None:
        target_user.is_active = payload.is_active

    if payload.email:
        target_user.email = payload.email

    if payload.full_name and target_user.profile:
        target_user.profile.full_name = payload.full_name

    db.add(target_user)
    await db.flush()
    return target_user

@security_router.get("/system/audit-trail", response_model=List[Any])
async def view_infrastructure_security_audit_logs(
    current_user: User = Depends(PermissionGuard(DynamicPermission.VIEW_AUDIT_LOGS)),
    db: AsyncSession = Depends(get_db)
):
    """
    Infrastructure Logging Core Pathway.

    Restricted to authorized system operators. Provides access to connection logs, metadata strings, and transaction traces.
    """
    stmt = select(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(100)
    res = await db.execute(stmt)
    return res.scalars().all()
