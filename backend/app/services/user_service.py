"""Account lifecycle: registration, authentication, sessions and passwords."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.email import AsyncEmailEngine
from app.core.roles import effective_role, is_platform_owner
from app.core.exceptions import AppBaseException, AuthenticationError, AuthorizationError, ConflictError
from app.core.security import (
    burn_password_check,
    create_token_pair,
    generate_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    verify_jwt_token,
    verify_password,
)
from app.models.activity import ActivityCategory
from app.models.base import AccountApprovalStatus, Profile, Role, User, UserRole, UserSession
from app.services import activity_service, approval_service

logger = logging.getLogger("educore.accounts")

# Two separate sign-in portals. Learners (students and parents) use the public pages;
# staff (teachers, administrators, the Super Admin) use the staff portal. An account can
# only sign in, or be created, through its own portal.
LEARNER_PORTAL = "learner"
STAFF_PORTAL = "staff"
PORTAL_ROLES = {
    LEARNER_PORTAL: frozenset({UserRole.STUDENT.value, UserRole.PARENT.value}),
    STAFF_PORTAL: frozenset({
        UserRole.TEACHER.value, UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value, UserRole.SCHOOL_ADMIN.value,
    }),
}
# Roles each portal may create at sign-up. Teachers and administrators are created as
# pending applications (see approval_service); the Super Admin role is never self-assigned.
PORTAL_SIGNUP_ROLES = {
    LEARNER_PORTAL: frozenset({UserRole.STUDENT, UserRole.PARENT}),
    STAFF_PORTAL: frozenset({UserRole.TEACHER, UserRole.ADMIN}),
}
WRONG_PORTAL_MESSAGES = {
    LEARNER_PORTAL: "This is a staff account. Please sign in through the staff portal.",
    STAFF_PORTAL: "This is a student or parent account. Please sign in on the main login page.",
}


def normalize_email(email: str) -> str:
    return email.strip().lower()


def role_value(user: User) -> str:
    return effective_role(user) or UserRole.STUDENT.value


def serialize_user(user: User) -> dict:
    """The single public representation of a user, matching the frontend `User` type."""
    profile = getattr(user, "profile", None)
    full_name = (profile.full_name if profile else "") or ""
    first, _, last = full_name.partition(" ")
    return {
        "id": user.id,
        "email": user.email,
        "first_name": first,
        "last_name": last,
        "full_name": full_name,
        "phone": (profile.phone_number if profile else None) or "",
        "avatar_url": profile.avatar_url if profile else None,
        "role": role_value(user),
        "is_active": user.is_active,
        "is_verified": bool(getattr(user, "is_verified", False)),
        "approval_status": _approval_value(user),
        "date_joined": user.created_at.isoformat() if user.created_at else "",
        "last_login_at": user.last_login_at.isoformat() if getattr(user, "last_login_at", None) else None,
        "profile": None,
    }


def _approval_value(user: User) -> str:
    status = getattr(user, "approval_status", None) or AccountApprovalStatus.APPROVED
    return status.value if isinstance(status, AccountApprovalStatus) else str(status)


def ensure_can_sign_in(user: User) -> None:
    """Raise unless the account is active and approved."""
    if not user.is_active:
        raise AuthorizationError("Your account has been deactivated. Contact support for help.")
    status = _approval_value(user)
    if status == AccountApprovalStatus.PENDING.value:
        raise AuthorizationError(approval_service.pending_message(UserRole(role_value(user))))
    if status == AccountApprovalStatus.REJECTED.value:
        note = f" Reason: {user.review_note}" if getattr(user, "review_note", None) else ""
        raise AuthorizationError(f"Your account application was not approved.{note}")


async def get_role(db: AsyncSession, role: UserRole) -> Role:
    role_entity = (await db.execute(select(Role).where(Role.name == role.value))).scalar_one_or_none()
    if role_entity is None:
        # Roles are seeded by migration 20261104090000; create on demand as a safety net.
        role_entity = Role(name=role.value)
        db.add(role_entity)
        await db.flush()
    return role_entity


async def _open_session(db: AsyncSession, user: User, user_agent: Optional[str], ip: Optional[str]) -> dict:
    tokens = create_token_pair(user.id)
    db.add(UserSession(
        user_id=user.id,
        refresh_token=tokens["refresh"],
        user_agent=(user_agent or "")[:255] or None,
        ip_address=(ip or "")[:45] or None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    await db.flush()
    return tokens


async def register_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
    phone: Optional[str],
    role: UserRole,
    portal: str = LEARNER_PORTAL,
    user_agent: Optional[str] = None,
    ip: Optional[str] = None,
) -> dict:
    if role not in PORTAL_SIGNUP_ROLES[portal]:
        raise AuthorizationError("That account type cannot be created here.")

    email = normalize_email(email)
    if (await db.execute(select(User.id).where(User.email == email))).scalar_one_or_none():
        raise ConflictError("An account with this e-mail address already exists. Try logging in instead.")

    needs_review = approval_service.requires_approval(role)
    role_entity = await get_role(db, role)
    verification_token = generate_token()
    user = User(
        email=email,
        hashed_password=hash_password(password),
        role_id=role_entity.id,
        verification_token=hash_token(verification_token),
        is_verified=False,
        approval_status=AccountApprovalStatus.PENDING if needs_review else AccountApprovalStatus.APPROVED,
    )
    user.role = role_entity
    user.profile = Profile(full_name=full_name[:100], phone_number=phone or None, metadata_fields={})
    db.add(user)
    await db.flush()

    await AsyncEmailEngine.send_verification_email(user.email, verification_token)
    logger.info("Registered user %s with role %s (pending=%s)", user.id, role.value, needs_review)

    if needs_review:
        # No session until a reviewer approves the account.
        await approval_service.on_application_submitted(db, user, role)
        return {
            "tokens": None,
            "user": serialize_user(user),
            "requires_approval": True,
            "message": approval_service.pending_message(role),
        }

    activity_service.record(
        db, action="account.registered", category=ActivityCategory.ACCOUNT,
        summary=f"{user.email} registered as {role.value}", actor=user,
        target_type="user", target_id=user.id,
    )
    tokens = await _open_session(db, user, user_agent, ip)
    return {"tokens": tokens, "user": serialize_user(user), "requires_approval": False, "message": None}


async def authenticate(db: AsyncSession, *, email: str, password: str, portal: str = LEARNER_PORTAL,
                       user_agent: Optional[str] = None, ip: Optional[str] = None) -> dict:
    email = normalize_email(email)
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        if user is None:
            burn_password_check(password)
        # Written in its own transaction: the request rolls back when we raise.
        await activity_service.record_detached(
            action="auth.login_failed", category=ActivityCategory.AUTH,
            summary=f"Failed sign-in for {email[:200]}",
            actor_id=user.id if user else None, actor_email=email[:255],
            actor_role=role_value(user) if user else None, status_code=401,
            details={"reason": "unknown_account" if user is None else "wrong_password"},
        )
        raise AuthenticationError("Incorrect e-mail or password.")

    if role_value(user) not in PORTAL_ROLES[portal]:
        await activity_service.record_detached(
            action="auth.login_blocked", category=ActivityCategory.AUTH,
            summary=f"{user.email} tried to sign in through the {portal} portal",
            actor_id=user.id, actor_email=user.email, actor_role=role_value(user), status_code=403,
            details={"reason": "wrong_portal", "portal": portal},
        )
        raise AuthorizationError(WRONG_PORTAL_MESSAGES[portal])

    try:
        ensure_can_sign_in(user)
    except AuthorizationError:
        await activity_service.record_detached(
            action="auth.login_blocked", category=ActivityCategory.AUTH,
            summary=f"Blocked sign-in for {user.email} ({_approval_value(user)}, active={user.is_active})",
            actor_id=user.id, actor_email=user.email, actor_role=role_value(user), status_code=403,
            details={"approval_status": _approval_value(user), "is_active": user.is_active},
        )
        raise

    if password_needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(password)
    user.last_login_at = datetime.now(timezone.utc)

    tokens = await _open_session(db, user, user_agent, ip)
    activity_service.record(
        db, action="auth.login", category=ActivityCategory.AUTH,
        summary=f"{user.email} signed in", actor=user, target_type="user", target_id=user.id,
    )
    return {"tokens": tokens, "user": serialize_user(user)}


async def rotate_refresh_token(db: AsyncSession, refresh_token: str) -> dict:
    payload = verify_jwt_token(refresh_token, is_refresh=True)
    session = (await db.execute(
        select(UserSession).where(UserSession.refresh_token == refresh_token).with_for_update()
    )).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if session is None:
        raise AuthenticationError("Your session has expired. Please log in again.")
    if session.is_revoked:
        # A revoked token being replayed indicates theft: revoke every session of the user.
        await revoke_all_sessions(db, session.user_id)
        # Commit now: the request-scoped session rolls back when we raise below,
        # which would silently undo the revocation.
        await db.commit()
        logger.warning("Refresh token reuse detected for user %s; all sessions revoked", session.user_id)
        raise AuthenticationError("Your session has expired. Please log in again.")
    if session.expires_at < now:
        raise AuthenticationError("Your session has expired. Please log in again.")

    user = (await db.execute(select(User).where(User.id == UUID(payload["sub"])))).scalar_one_or_none()
    if user is None or not user.is_active or _approval_value(user) != AccountApprovalStatus.APPROVED.value:
        raise AuthenticationError("Your account is no longer active.")

    session.is_revoked = True
    return await _open_session(db, user, session.user_agent, session.ip_address)


async def logout(db: AsyncSession, refresh_token: str) -> None:
    session = (await db.execute(
        select(UserSession).where(UserSession.refresh_token == refresh_token)
    )).scalar_one_or_none()
    if session is None:
        return
    session.is_revoked = True
    user = (await db.execute(select(User).where(User.id == session.user_id))).scalar_one_or_none()
    if user is not None:
        activity_service.record(
            db, action="auth.logout", category=ActivityCategory.AUTH,
            summary=f"{user.email} signed out", actor=user,
        )


async def revoke_all_sessions(db: AsyncSession, user_id: UUID) -> None:
    await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.is_revoked.is_(False))
        .values(is_revoked=True)
    )


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Always succeeds silently so the endpoint cannot be used to discover accounts."""
    user = (await db.execute(select(User).where(User.email == normalize_email(email)))).scalar_one_or_none()
    if user is None or not user.is_active:
        return
    token = generate_token()
    user.reset_token = hash_token(token)
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_TTL_MINUTES
    )
    await AsyncEmailEngine.send_password_reset_email(user.email, token)


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    user = (await db.execute(
        select(User).where(
            User.reset_token == hash_token(token),
            User.reset_token_expires > datetime.now(timezone.utc),
        )
    )).scalar_one_or_none()
    if user is None:
        raise AppBaseException("This reset link is invalid or has expired. Request a new one.", 400)
    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await revoke_all_sessions(db, user.id)
    activity_service.record(
        db, action="auth.password_reset", category=ActivityCategory.AUTH,
        summary=f"{user.email} reset their password", actor=user,
    )


async def verify_email(db: AsyncSession, token: str) -> None:
    user = (await db.execute(
        select(User).where(User.verification_token == hash_token(token))
    )).scalar_one_or_none()
    if user is None:
        raise AppBaseException("This verification link is invalid or has already been used.", 400)
    user.is_verified = True
    user.verification_token = None


async def change_password(db: AsyncSession, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise AppBaseException("Your current password is incorrect.", 400)
    if current_password == new_password:
        raise AppBaseException("Choose a new password that differs from the current one.", 400)
    user.hashed_password = hash_password(new_password)
    await revoke_all_sessions(db, user.id)
    activity_service.record(
        db, action="auth.password_changed", category=ActivityCategory.AUTH,
        summary=f"{user.email} changed their password", actor=user,
    )


async def deactivate_account(db: AsyncSession, user: User) -> None:
    """
    Self-service account deletion.

    Payment and content records reference users with ON DELETE RESTRICT (financial
    audit trail), so a hard delete fails. Instead the account is deactivated and its
    personal data anonymised, which honours erasure requests under the Kenya Data
    Protection Act while keeping the ledger intact.
    """
    if is_platform_owner(user):
        raise AuthorizationError("The platform owner account cannot be deleted.")
    activity_service.record(
        db, action="account.deleted", category=ActivityCategory.ACCOUNT,
        summary=f"{user.email} deleted their account", actor=user,
        target_type="user", target_id=user.id,
    )
    user.is_active = False
    user.email = f"deleted-{user.id.hex}@deleted.educore.invalid"
    user.hashed_password = hash_password(generate_token())
    user.verification_token = None
    user.reset_token = None
    if user.profile:
        user.profile.full_name = "Deleted user"
        user.profile.phone_number = None
        user.profile.avatar_url = None
        user.profile.metadata_fields = {}
    await revoke_all_sessions(db, user.id)
