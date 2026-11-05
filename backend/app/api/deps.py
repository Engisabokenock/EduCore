import logging
import time
from typing import Iterable, Optional

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.cache import get_redis_client
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppBaseException, AuthenticationError, AuthorizationError
from app.core.network import get_client_ip
from app.core.roles import effective_role, role_is_downgraded
from app.core.security import verify_jwt_token
from app.models.base import AccountApprovalStatus, DynamicPermission, User, UserRole

logger = logging.getLogger("educore.deps")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

STAFF_ROLES = (UserRole.SUPER_ADMIN, UserRole.ADMIN)


# ── Authentication ───────────────────────────────────────────────────────────

async def _load_active_user(token: str, db: AsyncSession) -> User:
    payload = verify_jwt_token(token, is_refresh=False)
    user = (await db.execute(select(User).where(User.id == payload["sub"]))).scalar_one_or_none()
    if not user:
        raise AuthenticationError("Your account could not be found. Please log in again.")
    if not user.is_active:
        raise AuthorizationError("Your account has been deactivated. Contact support for help.")
    if user.approval_status != AccountApprovalStatus.APPROVED:
        # Tokens issued before an approval was revoked must stop working too.
        raise AuthorizationError("Your account is not approved yet.")
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await _load_active_user(token, db)


# Backwards-compatible alias used by several routers.
get_current_active_user = get_current_user


async def get_optional_user(
    token: Optional[str] = Depends(optional_oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Resolve the user when a valid bearer token is present, otherwise None.

    Used by public endpoints (free downloads, resource access checks) that behave
    differently for signed-in users but must still work anonymously.
    """
    if not token:
        return None
    try:
        return await _load_active_user(token, db)
    except (AuthenticationError, AuthorizationError):
        return None


def role_of(user: Optional[User]) -> Optional[str]:
    return effective_role(user)


def has_role(user: Optional[User], roles: Iterable[UserRole]) -> bool:
    current = role_of(user)
    return current is not None and current in {r.value for r in roles}


def is_staff(user: Optional[User]) -> bool:
    return has_role(user, STAFF_ROLES)


# ── Authorization ────────────────────────────────────────────────────────────

class RoleChecker:
    """
    Role-based guard. SUPER_ADMIN is the platform owner and always passes, so it is
    never accidentally locked out of an ADMIN-only route.
    """

    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = set(allowed_roles) | {UserRole.SUPER_ADMIN}

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not has_role(current_user, self.allowed_roles):
            raise AuthorizationError()
        return current_user


class PermissionGuard:
    """
    Capability-based guard. SUPER_ADMIN bypasses all checks; every other role must
    hold the specific DynamicPermission through its role assignment.
    """

    def __init__(self, required_permission: DynamicPermission):
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if has_role(current_user, [UserRole.SUPER_ADMIN]):
            return current_user
        # A super_admin role row on a non-owner account grants nothing.
        permissions = [] if role_is_downgraded(current_user) else (
            current_user.role.permissions if current_user.role else []
        )
        assigned = {p.name for p in permissions}
        if self.required_permission not in assigned:
            raise AuthorizationError(
                f"This action requires the '{self.required_permission.value}' permission."
            )
        return current_user


# Kept for compatibility with existing imports.
PermissionChecker = PermissionGuard


# ── Rate limiting ────────────────────────────────────────────────────────────

_LOCAL_BUCKETS: dict[str, tuple[int, int]] = {}
_LOCAL_MAX_KEYS = 50_000
_WINDOW_SECONDS = 60


async def _hit(bucket: str, limit: int) -> None:
    """
    Fixed-window counter keyed per client and minute. Uses Redis (shared across all
    API instances) and falls back to process memory if Redis is unavailable.
    """
    window = int(time.time() // _WINDOW_SECONDS)
    key = f"rl:{bucket}:{window}"

    client = get_redis_client()
    if client is not None:
        try:
            async with client:
                pipe = client.pipeline()
                pipe.incr(key)
                pipe.expire(key, _WINDOW_SECONDS + 5)
                count, _ = await pipe.execute()
            if count > limit:
                raise AppBaseException("Too many requests. Please slow down and try again shortly.", 429)
            return
        except AppBaseException:
            raise
        except Exception as exc:
            logger.debug("Redis rate limiter unavailable, using local fallback: %s", exc)

    if len(_LOCAL_BUCKETS) > _LOCAL_MAX_KEYS:
        stale = [k for k, (w, _) in _LOCAL_BUCKETS.items() if w != window]
        for k in stale:
            _LOCAL_BUCKETS.pop(k, None)
    stored_window, count = _LOCAL_BUCKETS.get(bucket, (window, 0))
    count = count + 1 if stored_window == window else 1
    _LOCAL_BUCKETS[bucket] = (window, count)
    if count > limit:
        raise AppBaseException("Too many requests. Please slow down and try again shortly.", 429)


async def sliding_window_rate_limiter(request: Request) -> None:
    """Global per-IP request budget applied to every API route."""
    await _hit(f"global:{get_client_ip(request)}", settings.RATE_LIMIT_PER_MINUTE)


async def auth_rate_limiter(request: Request) -> None:
    """Tight budget for credential endpoints to blunt brute force and enumeration."""
    await _hit(f"auth:{request.url.path}:{get_client_ip(request)}", settings.AUTH_RATE_LIMIT_PER_MINUTE)


def generate_paginated_cache_key(endpoint: str, request: Request) -> str:
    query_string = request.url.query
    return f"cache:page:{endpoint}:{query_string if query_string else 'default'}"
