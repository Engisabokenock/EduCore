from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from typing import Optional
from app.models.base import UserRole

class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Secured application standards dictate min length 8")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    role: UserRole = UserRole.STUDENT
    password_confirm: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Cryptographic reset token value")
    new_password: str = Field(..., min_length=8)

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=30)
    avatar_url: Optional[str] = Field(None, max_length=512)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class ProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    full_name: str
    phone_number: Optional[str]
    avatar_url: Optional[str]

class UserAccountSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    role_name: UserRole = Field(alias="role_name_extractor")
    is_verified: bool
    profile: ProfileSchema

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Flatten role property access mapping for presentation serialization
        if hasattr(obj, "role") and obj.role:
            setattr(obj, "role_name_extractor", obj.role.name)
        else:
            setattr(obj, "role_name_extractor", UserRole.STUDENT)
        return super().model_validate(obj, **kwargs)
