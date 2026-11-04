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
from app.models.base import Profile, Role, User, UserRole, UserSession

logger = logging.getLogger("educore.accounts")

# Roles a member of the public may pick at sign-up. Staff roles are only ever
# granted by an administrator through the security control plane.
SELF_SERVICE_ROLES = {UserRole.STUDENT, UserRole.TEACHER, UserRole.PARENT}


def normalize_email(email: str) -> str:
    return email.strip().lower()


def role_value(user: User) -> str:
    role = getattr(user, "role", None)
    if role is None:
        return UserRole.STUDENT.value
    name = role.name
    return name.value if isinstance(name, UserRole) else str(name)


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
        "date_joined": user.created_at.isoformat() if user.created_at else "",
        "last_login_at": user.last_login_at.isoformat() if getattr(user, "last_login_at", None) else None,
        "profile": None,
    }


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
    user_agent: Optional[str] = None,
    ip: Optional[str] = None,
) -> dict:
    if role not in SELF_SERVICE_ROLES:
        raise AuthorizationError("That account type cannot be created through public sign-up.")

    email = normalize_email(email)
    if (await db.execute(select(User.id).where(User.email == email))).scalar_one_or_none():
        raise ConflictError("An account with this e-mail address already exists. Try logging in instead.")

    role_entity = await get_role(db, role)
    verification_token = generate_token()
    user = User(
        email=email,
        hashed_password=hash_password(password),
        role_id=role_entity.id,
        verification_token=hash_token(verification_token),
        is_verified=False,
    )
    user.role = role_entity
    user.profile = Profile(full_name=full_name[:100], phone_number=phone or None, metadata_fields={})
    db.add(user)
    await db.flush()

    tokens = await _open_session(db, user, user_agent, ip)
    await AsyncEmailEngine.send_verification_email(user.email, verification_token)
    logger.info("Registered user %s with role %s", user.id, role.value)
    return {"tokens": tokens, "user": serialize_user(user)}


async def authenticate(db: AsyncSession, *, email: str, password: str,
                       user_agent: Optional[str] = None, ip: Optional[str] = None) -> dict:
    user = (await db.execute(select(User).where(User.email == normalize_email(email)))).scalar_one_or_none()
    if user is None:
        burn_password_check(password)
        raise AuthenticationError("Incorrect e-mail or password.")
    if not verify_password(password, user.hashed_password):
        raise AuthenticationError("Incorrect e-mail or password.")
    if not user.is_active:
        raise AuthorizationError("Your account has been deactivated. Contact support for help.")

    if password_needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(password)
    user.last_login_at = datetime.now(timezone.utc)

    tokens = await _open_session(db, user, user_agent, ip)
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
    if user is None or not user.is_active:
        raise AuthenticationError("Your account is no longer active.")

    session.is_revoked = True
    return await _open_session(db, user, session.user_agent, session.ip_address)


async def logout(db: AsyncSession, refresh_token: str) -> None:
    await db.execute(
        update(UserSession).where(UserSession.refresh_token == refresh_token).values(is_revoked=True)
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


async def deactivate_account(db: AsyncSession, user: User) -> None:
    """
    Self-service account deletion.

    Payment and content records reference users with ON DELETE RESTRICT (financial
    audit trail), so a hard delete fails. Instead the account is deactivated and its
    personal data anonymised, which honours erasure requests under the Kenya Data
    Protection Act while keeping the ledger intact.
    """
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
