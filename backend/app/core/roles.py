"""
Effective role resolution.

The Super Admin role is reserved for a single platform owner, identified by
``settings.PLATFORM_OWNER_EMAIL``. Any other account that holds the ``super_admin``
role (for example through a manual database edit) is treated as a student and gets
no permissions, so the owner's authority cannot be duplicated by changing a row.

Every role check in the API goes through ``effective_role``.
"""
from typing import Optional

from app.core.config import settings
from app.models.base import User, UserRole


def owner_email() -> str:
    return settings.PLATFORM_OWNER_EMAIL.strip().lower()


def is_platform_owner(user: Optional[User]) -> bool:
    return bool(user is not None and owner_email() and (user.email or "").strip().lower() == owner_email())


def raw_role(user: Optional[User]) -> Optional[str]:
    role = getattr(user, "role", None) if user is not None else None
    if role is None:
        return None
    name = role.name
    return str(name.value if isinstance(name, UserRole) else name)


def effective_role(user: Optional[User]) -> Optional[str]:
    """The role the user actually acts with."""
    role = raw_role(user)
    if role == UserRole.SUPER_ADMIN.value and not is_platform_owner(user):
        return UserRole.STUDENT.value
    return role


def role_is_downgraded(user: Optional[User]) -> bool:
    return raw_role(user) != effective_role(user)
