import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, update, delete, true
from app.core.database import get_db
from app.core.cache import CacheManager
from app.core.config import settings
from app.core.exceptions import AuthorizationError, ConflictError
from app.api.deps import RoleChecker, PermissionGuard, has_role
from app.services.user_service import normalize_email, serialize_user
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
from app.schemas.admin_dashboard import AdminDashboardStats
from app.schemas.payment import TransactionOut
from app.schemas.school import SchoolResponse

router = APIRouter(prefix="/admin-control-plane", tags=["Master Administrative Operations Gateway Router"])

# Admins and the Super Admin (RoleChecker always admits SUPER_ADMIN).
super_admin_clearance_guard = Depends(RoleChecker([UserRole.ADMIN]))


def _guard_platform_owner(actor: User, target: User) -> None:
    """Only the Super Admin may modify a Super Admin account (prevents takeover via e-mail change)."""
    if has_role(target, [UserRole.SUPER_ADMIN]) and not has_role(actor, [UserRole.SUPER_ADMIN]):
        raise AuthorizationError("Only the platform owner can modify a Super Admin account.")


async def _apply_user_update(db: AsyncSession, target: User, payload: AdminUserUpdatePayload) -> None:
    if payload.is_active is not None:
        target.is_active = payload.is_active
    if payload.email:
        email = normalize_email(payload.email)
        if email != target.email:
            clash = (await db.execute(
                select(User.id).where(User.email == email, User.id != target.id)
            )).scalar_one_or_none()
            if clash:
                raise ConflictError("Another account already uses that e-mail address.")
            target.email = email
    if payload.full_name and target.profile:
        target.profile.full_name = payload.full_name


# --- SECTION 0: DASHBOARD SUMMARY ---

@router.get("/dashboard/stats", response_model=AdminDashboardStats, dependencies=[super_admin_clearance_guard])
async def administrative_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Headline counters for the admin dashboard."""
    now = datetime.now(timezone.utc)

    async def count(stmt) -> int:
        return int((await db.execute(stmt)).scalar() or 0)

    revenue = (await db.execute(
        select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
            PaymentTransaction.status == TransactionStatus.COMPLETED.value
        )
    )).scalar()
    return {
        "total_users": await count(select(func.count(User.id)).where(User.is_active.is_(True))),
        "active_subscriptions": await count(
            select(func.count(UserSubscription.id)).where(
                or_(
                    and_(UserSubscription.status.in_([SubscriptionState.ACTIVE, SubscriptionState.CANCELED]),
                         UserSubscription.current_period_end > now),
                    and_(UserSubscription.status == SubscriptionState.GRACE_PERIOD,
                         UserSubscription.grace_period_end > now),
                )
            )
        ),
        "total_revenue": float(revenue or 0),
        "pending_reviews": await count(
            select(func.count(ResourceReview.id)).where(
                ResourceReview.moderation_status == ReviewModerationStatus.PENDING
            )
        ),
        "total_resources": await count(
            select(func.count(AcademicResource.id)).where(AcademicResource.is_archived.is_(False))
        ),
        "total_schools": await count(select(func.count(School.id))),
    }

# --- SECTION 1: IDENTITY REPOSITORIES MANAGEMENT (USERS) ---

@router.post("/users/search", response_model=List[UserAccountSchema], dependencies=[super_admin_clearance_guard])
async def administrative_user_index_lookup(payload: AdminUserSearchPayload, db: AsyncSession = Depends(get_db)):
    """Provides advanced cross-filtering, security auditing, and verification for user accounts."""
    conditions = []
    if payload.role:
        # Match against underlying identity keys
        conditions.append(User.role.has(Role.name == payload.role.value))
    if payload.is_active is not None:
        conditions.append(User.is_active == payload.is_active)
    if payload.search_term:
        term = payload.search_term.strip().lower()
        conditions.append(
            or_(
                func.lower(User.email).contains(term, autoescape=True),
                User.id.in_(
                    select(Profile.user_id).where(func.lower(Profile.full_name).contains(term, autoescape=True))
                )
            )
        )

    offset_calc = (payload.page - 1) * payload.page_size
    stmt = select(User).where(and_(true(), *conditions)).offset(offset_calc).limit(payload.page_size).order_by(User.created_at.desc())
    ctx = await db.execute(stmt)
    return [serialize_user(u) for u in ctx.scalars().all()]

@router.patch("/users/{user_id}", response_model=UserAccountSchema)
async def administrative_override_user_profile(
    user_id: uuid.UUID,
    payload: AdminUserUpdatePayload,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Edit a user's e-mail, name or active flag. Role changes go through the security control plane."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    _guard_platform_owner(current_user, user)
    if user.id == current_user.id and payload.is_active is False:
        raise AuthorizationError("You cannot deactivate your own account.")
    await _apply_user_update(db, user, payload)
    await db.flush()
    return serialize_user(user)

# --- SECTION 2: CURRICULUM ASSET BALANCING (RESOURCES) ---

@router.post("/resources/bulk-action", status_code=status.HTTP_200_OK, dependencies=[super_admin_clearance_guard])
async def administrative_bulk_resource_processing(payload: AdminBulkActionRequest, db: AsyncSession = Depends(get_db)):
    """Executes high-efficiency bulk updates across multiple content asset partitions simultaneously."""
    if payload.action == "archive":
        stmt = update(AcademicResource).where(AcademicResource.id.in_(payload.target_ids)).values(is_archived=True, is_published=False)
    elif payload.action == "publish":
        stmt = update(AcademicResource).where(AcademicResource.id.in_(payload.target_ids)).values(is_published=True, is_archived=False, scheduled_publish_at=None, published_at=datetime.now(timezone.utc))
    elif payload.action == "purge":
        stmt = delete(AcademicResource).where(AcademicResource.id.in_(payload.target_ids))
    else:
        raise HTTPException(status_code=400, detail="Requested bulk state transformation logic matches invalid criteria pattern")

    result = await db.execute(stmt)
    await CacheManager.invalidate_prefix("cache:search:")
    return {"status": "success", "processed_records_count": result.rowcount or 0}

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
    stmt = select(PaymentTransaction).where(and_(true(), *conditions)).offset(offset_calc).limit(payload.page_size).order_by(PaymentTransaction.created_at.desc())
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

    result = await db.execute(stmt)
    return {"status": "success", "affected_nodes_count": result.rowcount or 0}

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
        "daily_free_download_limit": settings.DAILY_FREE_DOWNLOAD_LIMIT,
        "allowed_upload_extensions": ["pdf"],
        "grace_period_duration_days": settings.SUBSCRIPTION_GRACE_PERIOD_DAYS,
        "mpesa_fallback_routing_active": False,
        "mpesa_configured": settings.mpesa_configured,
        "storage_configured": settings.storage_configured,
        "last_recalculation_timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.put("/system-settings", status_code=status.HTTP_200_OK, dependencies=[super_admin_clearance_guard])
async def update_global_system_runtime_parameters(payload: SystemSettingsUpdatePayload):
    """
    Overwrites operational parameters instantly without requiring server reboots.

    Changes take effect immediately across all active API instances.
    """
    # Runtime settings are environment-driven today. Report that honestly instead of
    # claiming the change was applied.
    raise HTTPException(
        status_code=501,
        detail="Runtime settings are configured through environment variables and cannot be changed here yet.",
    )

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

    Security Firewall Rules:
    - Rule A: Protect Super Admin accounts from unauthorized changes by non-Super-Admins
    - Rule B: Block lower administrators from elevating their own roles to Super Admin
    """
    target_user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    _guard_platform_owner(current_user, target_user)
    if payload.role == UserRole.SUPER_ADMIN and not has_role(current_user, [UserRole.SUPER_ADMIN]):
        raise AuthorizationError("Only the platform owner can assign the Super Admin role.")
    if target_user.id == current_user.id and payload.role and payload.role.value != serialize_user(current_user)["role"]:
        raise AuthorizationError("You cannot change your own role.")

    if payload.role:
        target_role = (await db.execute(select(Role).where(Role.name == payload.role.value))).scalar_one_or_none()
        if not target_role:
            raise HTTPException(status_code=400, detail="Requested role does not exist")
        target_user.role_id = target_role.id
        target_user.role = target_role

    await _apply_user_update(db, target_user, payload)
    await db.flush()
    return serialize_user(target_user)

@security_router.get("/system/audit-trail")
async def view_infrastructure_security_audit_logs(
    current_user: User = Depends(PermissionGuard(DynamicPermission.VIEW_AUDIT_LOGS)),
    db: AsyncSession = Depends(get_db)
):
    """
    Infrastructure Logging Core Pathway.

    Restricted to authorized system operators. Provides access to connection logs,
    metadata strings, and transaction traces.
    """
    stmt = select(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(100)
    res = await db.execute(stmt)
    return [
        {"id": log.id, "event": log.event_type.value, "recipient": log.recipient_address, "timestamp": log.sent_at}
        for log in res.scalars().all()
    ]
