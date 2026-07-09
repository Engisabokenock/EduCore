import time
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import verify_jwt_token
from app.core.exceptions import AuthenticationError, AuthorizationError, AppBaseException
from app.models.base import User, UserRole, DynamicPermission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Decrypts context strings and secures persistent user entity identities from data containers."""
    payload = verify_jwt_token(token, is_refresh=False)
    user_id = payload.get("sub")

    query = select(User).where(User.id == user_id)
    execution_context = await db.execute(query)
    user = execution_context.scalar_one_or_none()

    if not user:
        raise AuthenticationError("Active user session context dropped or profile matching identifier missing")
    if not user.is_active:
        raise AuthorizationError("Access denied: Your operational account identity profile status is frozen")

    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = verify_jwt_token(token, is_refresh=False)
    user_id = payload.get("sub")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise AuthenticationError("User resource either deactivated or missing")
    return user

class RoleChecker:
    """RBAC dynamic assertion check structural enforcement."""
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in self.allowed_roles:
            raise AuthorizationError("Your access layer profiles block entry to this routing path")
        return current_user


class PermissionChecker:
    """Granular Capability-Based Access Control Validation Core."""
    def __init__(self, required_permission: str | DynamicPermission):
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        user_permissions = {p.name for p in current_user.role.permissions}
        required = self.required_permission
        if isinstance(required, str):
            try:
                required = DynamicPermission(required)
            except ValueError:
                pass
        if required not in user_permissions:
            raise AuthorizationError(f"Required privilege constraint missing: {self.required_permission}")
        return current_user


class PermissionGuard:
    """
    Production-grade Granular RBAC Verification Layer.

    Validates identity access vectors. Bypasses checks for Super Admin profiles,
    while enforcing explicit capability validation for Admin and lower roles.
    """
    def __init__(self, required_permission: DynamicPermission):
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.name == UserRole.SUPER_ADMIN:
            return current_user

        assigned_permissions = {p.name for p in current_user.role.permissions}
        if self.required_permission not in assigned_permissions:
            raise AuthorizationError(
                f"Security compliance violation: Account requires privilege level token key '{self.required_permission.value}'"
            )

        return current_user

# Simple, high-performance in-memory dictionary for sliding-window rate limiting.
# For distributed multi-node production setups, swap this out for an atomic Redis token bucket.
RATE_LIMIT_STORAGE: dict[str, list[float]] = {}
LIMIT_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 60  # 60 requests per minute configuration threshold


async def sliding_window_rate_limiter(request: Request) -> None:
    """
    Protects API endpoints from Brute Force and Denial of Service (DoS) attacks.

    Implements a strict sliding-window rate limiter mapped against the client's IP signature.
    """
    client_ip = request.client.host if request.client else "0.0.0.0"
    current_timestamp = time.time()

    if client_ip not in RATE_LIMIT_STORAGE:
        RATE_LIMIT_STORAGE[client_ip] = []

    # Evict expired request timestamps outside the sliding window
    RATE_LIMIT_STORAGE[client_ip] = [
        ts for ts in RATE_LIMIT_STORAGE[client_ip]
        if current_timestamp - ts < LIMIT_WINDOW_SECONDS
    ]

    # Free the bucket once it is empty to avoid unbounded memory growth
    if not RATE_LIMIT_STORAGE[client_ip]:
        RATE_LIMIT_STORAGE.pop(client_ip, None)

    if client_ip in RATE_LIMIT_STORAGE and len(RATE_LIMIT_STORAGE[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        raise AppBaseException("Too Many Requests: Rate limit exceeded for this time window", 429)

    RATE_LIMIT_STORAGE.setdefault(client_ip, []).append(current_timestamp)


def generate_paginated_cache_key(endpoint: str, request: Request) -> str:
    """Compiles an immutable unique cache signature tracking paginated query string vectors."""
    query_string = request.url.query
    return f"cache:page:{endpoint}:{query_string if query_string else 'default'}"
