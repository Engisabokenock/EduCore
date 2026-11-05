"""
Staff-reviewed sign-ups.

Policy:

* Students and parents are active as soon as they register.
* Teachers register as *pending* and are approved or rejected by an Admin (or the
  Super Admin).
* Administrators register as *pending* and only the Super Admin can approve them.

A pending or rejected account cannot sign in. Every decision is written to the activity
log and the applicant is notified.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import AsyncEmailEngine
from app.core.exceptions import AppBaseException, AuthorizationError, NotFoundError
from app.models.activity import ActivityCategory
from app.models.base import AccountApprovalStatus, Role, User, UserRole
from app.models.notification import NotificationChannel, NotificationEvent, NotificationLog
from app.services import activity_service

logger = logging.getLogger("educore.approvals")

# Requested role -> roles allowed to review that application.
APPROVERS: dict[UserRole, frozenset[UserRole]] = {
    UserRole.TEACHER: frozenset({UserRole.ADMIN, UserRole.SUPER_ADMIN}),
    UserRole.ADMIN: frozenset({UserRole.SUPER_ADMIN}),
}

ROLE_LABELS = {
    UserRole.TEACHER: "teacher",
    UserRole.ADMIN: "administrator",
}


def requires_approval(role: UserRole) -> bool:
    return role in APPROVERS


def _role(user: User) -> Optional[UserRole]:
    if user is None or user.role is None:
        return None
    try:
        return UserRole(user.role.name.value if isinstance(user.role.name, UserRole) else user.role.name)
    except ValueError:
        return None


def reviewable_roles(actor: User) -> set[UserRole]:
    """Roles whose applications ``actor`` may decide on."""
    actor_role = _role(actor)
    return {requested for requested, approvers in APPROVERS.items() if actor_role in approvers}


def pending_message(role: UserRole) -> str:
    reviewer = "the Super Admin" if role == UserRole.ADMIN else "an administrator"
    return (
        f"Your {ROLE_LABELS.get(role, role.value)} account has been created and is waiting for approval "
        f"by {reviewer}. You can sign in once it is approved."
    )


def serialize_application(user: User) -> dict:
    from app.services.user_service import serialize_user

    data = serialize_user(user)
    data.update({
        "approval_status": user.approval_status.value if user.approval_status else None,
        "reviewed_at": user.reviewed_at.isoformat() if user.reviewed_at else None,
        "reviewed_by_id": user.reviewed_by_id,
        "review_note": user.review_note,
    })
    return data


# ── Sign-up hook ─────────────────────────────────────────────────────────────

async def on_application_submitted(db: AsyncSession, applicant: User, role: UserRole) -> None:
    """Notify everyone who can review the application, in-app and by e-mail."""
    approver_roles = [r.value for r in APPROVERS[role]]
    approvers = (await db.execute(
        select(User).join(Role, Role.id == User.role_id).where(
            Role.name.in_(approver_roles),
            User.is_active.is_(True),
            User.approval_status == AccountApprovalStatus.APPROVED,
        )
    )).scalars().all()

    label = ROLE_LABELS[role]
    name = applicant.profile.full_name if applicant.profile else applicant.email
    for approver in approvers:
        db.add(NotificationLog(
            user_id=approver.id,
            event_type=NotificationEvent.ACCOUNT_REVIEW,
            channel=NotificationChannel.PUSH,
            recipient_address=approver.email[:255],
            title=f"New {label} application",
            body=f"{name} ({applicant.email}) applied for a {label} account and is waiting for your review.",
            data={"applicant_id": str(applicant.id), "requested_role": role.value},
            is_sent=True,
        ))
        await AsyncEmailEngine.send_application_alert(approver.email, applicant.email, label)

    await AsyncEmailEngine.send_application_received(applicant.email, label)
    activity_service.record(
        db,
        action="approval.requested",
        category=ActivityCategory.APPROVAL,
        summary=f"{applicant.email} applied for a {label} account",
        actor=applicant,
        target_type="user",
        target_id=applicant.id,
        details={"requested_role": role.value, "approvers_notified": len(approvers)},
    )


# ── Review queue ─────────────────────────────────────────────────────────────

async def list_applications(
    db: AsyncSession,
    actor: User,
    *,
    status: AccountApprovalStatus = AccountApprovalStatus.PENDING,
    role: Optional[UserRole] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    allowed = reviewable_roles(actor)
    if role is not None:
        if role not in allowed:
            raise AuthorizationError(f"You cannot review {ROLE_LABELS.get(role, role.value)} applications.")
        allowed = {role}
    if not allowed:
        raise AuthorizationError("You cannot review account applications.")

    conditions = (
        Role.name.in_([r.value for r in allowed]),
        User.approval_status == status,
    )
    base = select(User).join(Role, Role.id == User.role_id).where(*conditions)
    total = (await db.execute(
        select(func.count(User.id)).join(Role, Role.id == User.role_id).where(*conditions)
    )).scalar() or 0
    users = (await db.execute(
        base.order_by(User.created_at.asc() if status == AccountApprovalStatus.PENDING else User.reviewed_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return {
        "items": [serialize_application(u) for u in users],
        "total": int(total),
        "page": page,
        "page_size": page_size,
    }


async def pending_counts(db: AsyncSession, actor: User) -> dict:
    allowed = reviewable_roles(actor)
    rows = dict((await db.execute(
        select(Role.name, func.count(User.id))
        .join(Role, Role.id == User.role_id)
        .where(User.approval_status == AccountApprovalStatus.PENDING, Role.name.in_([r.value for r in allowed]))
        .group_by(Role.name)
    )).all()) if allowed else {}
    counts = {r.value: int(rows.get(r.value, 0)) for r in allowed}
    return {"total": sum(counts.values()), "by_role": counts}


async def _load_for_review(db: AsyncSession, actor: User, user_id: UUID) -> tuple[User, UserRole]:
    applicant = (await db.execute(
        select(User).where(User.id == user_id).with_for_update(of=User)
    )).scalar_one_or_none()
    if applicant is None:
        raise NotFoundError("Application not found.")
    requested = _role(applicant)
    if requested not in APPROVERS:
        raise AppBaseException("This account does not need approval.", 400)
    if requested not in reviewable_roles(actor):
        reviewer = "the Super Admin" if requested == UserRole.ADMIN else "an administrator"
        raise AuthorizationError(f"Only {reviewer} can review {ROLE_LABELS[requested]} applications.")
    if applicant.id == actor.id:
        raise AuthorizationError("You cannot review your own application.")
    return applicant, requested


def _notify_applicant(db: AsyncSession, applicant: User, approved: bool, label: str, note: Optional[str]) -> None:
    if approved:
        title, body = "Account approved", f"Your {label} account has been approved. You can now sign in."
    else:
        title = "Application not approved"
        body = f"Your {label} application was not approved." + (f" Reason: {note}" if note else "")
    db.add(NotificationLog(
        user_id=applicant.id,
        event_type=NotificationEvent.ACCOUNT_REVIEW,
        channel=NotificationChannel.PUSH,
        recipient_address=applicant.email[:255],
        title=title,
        body=body,
        data={"approved": approved},
        is_sent=True,
    ))


async def approve(db: AsyncSession, actor: User, user_id: UUID, note: Optional[str] = None) -> dict:
    applicant, requested = await _load_for_review(db, actor, user_id)
    if applicant.approval_status == AccountApprovalStatus.APPROVED:
        raise AppBaseException("This account is already approved.", 409)

    previous = applicant.approval_status
    applicant.approval_status = AccountApprovalStatus.APPROVED
    applicant.reviewed_by_id = actor.id
    applicant.reviewed_at = datetime.now(timezone.utc)
    applicant.review_note = (note or "").strip()[:500] or None
    applicant.is_active = True

    label = ROLE_LABELS[requested]
    _notify_applicant(db, applicant, True, label, applicant.review_note)
    await AsyncEmailEngine.send_account_review_result(applicant.email, label, approved=True, note=applicant.review_note)
    activity_service.record(
        db,
        action="approval.approved",
        category=ActivityCategory.APPROVAL,
        summary=f"Approved {applicant.email} as {label}",
        actor=actor,
        target_type="user",
        target_id=applicant.id,
        details={"requested_role": requested.value, "previous_status": previous.value, "note": applicant.review_note},
    )
    await db.flush()
    logger.info("User %s approved %s as %s", actor.id, applicant.id, requested.value)
    return serialize_application(applicant)


async def reject(db: AsyncSession, actor: User, user_id: UUID, note: Optional[str] = None) -> dict:
    applicant, requested = await _load_for_review(db, actor, user_id)
    if applicant.approval_status != AccountApprovalStatus.PENDING:
        raise AppBaseException("Only pending applications can be rejected.", 409)

    applicant.approval_status = AccountApprovalStatus.REJECTED
    applicant.reviewed_by_id = actor.id
    applicant.reviewed_at = datetime.now(timezone.utc)
    applicant.review_note = (note or "").strip()[:500] or None

    from app.services.user_service import revoke_all_sessions

    await revoke_all_sessions(db, applicant.id)
    label = ROLE_LABELS[requested]
    _notify_applicant(db, applicant, False, label, applicant.review_note)
    await AsyncEmailEngine.send_account_review_result(applicant.email, label, approved=False, note=applicant.review_note)
    activity_service.record(
        db,
        action="approval.rejected",
        category=ActivityCategory.APPROVAL,
        summary=f"Rejected {applicant.email}'s {label} application",
        actor=actor,
        target_type="user",
        target_id=applicant.id,
        details={"requested_role": requested.value, "note": applicant.review_note},
    )
    await db.flush()
    logger.info("User %s rejected %s (%s)", actor.id, applicant.id, requested.value)
    return serialize_application(applicant)
