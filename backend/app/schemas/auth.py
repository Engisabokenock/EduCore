from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.base import UserRole


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


# ── Frontend-aligned auth contract ────────────────────────────────────────────
# Register/login return { tokens: { access, refresh }, user }, refresh returns
# { access, refresh }, and the user shape matches the frontend `User` type.

class AuthTokensSchema(BaseModel):
    access: str
    refresh: str


class UserPublicSchema(BaseModel):
    id: UUID
    email: str
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    phone: str = ""
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool = True
    is_verified: bool = False
    date_joined: str = ""
    last_login_at: Optional[str] = None
    profile: Optional[dict] = None


class AuthResultSchema(BaseModel):
    tokens: AuthTokensSchema
    user: UserPublicSchema


class RefreshRequest(BaseModel):
    refresh: str = Field(..., min_length=10, max_length=2048)
