from pydantic import BaseModel, EmailStr, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.base import UserRole

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Strength requirement >= 8 characters")
    full_name: str = Field(min_length=2, max_length=100)
    role: UserRole = UserRole.STUDENT

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

# ── Frontend-aligned auth contract ────────────────────────────────────────────
# The Next.js client expects: { tokens: { access, refresh }, user: {...} } on
# register/login, { access, refresh } on refresh, and a User shape with
# first_name/last_name/date_joined. These schemas match that wire contract.

class AuthTokensSchema(BaseModel):
    access: str
    refresh: str

class UserPublicSchema(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    phone: str = ""
    role: UserRole
    is_verified: bool
    date_joined: str = ""
    profile: Optional[dict] = None

class AuthResultSchema(BaseModel):
    tokens: AuthTokensSchema
    user: UserPublicSchema

class RefreshRequest(BaseModel):
    refresh: str
