from typing import Optional

from pydantic import AliasChoices, BaseModel, EmailStr, Field, model_validator

from app.models.base import UserRole
from app.schemas.auth import UserPublicSchema

PASSWORD_FIELD = dict(min_length=8, max_length=128)


class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., **PASSWORD_FIELD)
    password_confirm: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    role: UserRole = UserRole.STUDENT

    @model_validator(mode="after")
    def _passwords_match(self):
        if self.password_confirm is not None and self.password_confirm != self.password:
            raise ValueError("Passwords do not match")
        return self


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=256)
    new_password: str = Field(..., **PASSWORD_FIELD)
    new_password_confirm: Optional[str] = None

    @model_validator(mode="after")
    def _passwords_match(self):
        if self.new_password_confirm is not None and self.new_password_confirm != self.new_password:
            raise ValueError("Passwords do not match")
        return self


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=30, validation_alias=AliasChoices("phone_number", "phone"))
    avatar_url: Optional[str] = Field(None, max_length=512)


class ChangePasswordRequest(BaseModel):
    # The frontend sends `old_password`; `current_password` is accepted too.
    current_password: str = Field(..., max_length=128, validation_alias=AliasChoices("current_password", "old_password"))
    new_password: str = Field(..., **PASSWORD_FIELD)
    new_password_confirm: Optional[str] = None

    @model_validator(mode="after")
    def _passwords_match(self):
        if self.new_password_confirm is not None and self.new_password_confirm != self.new_password:
            raise ValueError("Passwords do not match")
        return self


# A user account is always serialized through user_service.serialize_user.
UserAccountSchema = UserPublicSchema
