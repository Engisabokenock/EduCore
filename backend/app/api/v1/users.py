from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import auth_rate_limiter, get_current_user
from app.core.database import get_db
from app.models.base import User
from app.schemas.users import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ProfileUpdateRequest,
    ResetPasswordRequest,
    UserAccountSchema,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Self-Service & Profile Management Engine"])


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(auth_rate_limiter)])
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await user_service.request_password_reset(db, payload.email)
    return {"message": "If an account exists for that e-mail, a reset link has been sent."}


@router.post("/reset-password", dependencies=[Depends(auth_rate_limiter)])
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await user_service.reset_password(db, payload.token, payload.new_password)
    return {"message": "Your password has been reset. Please log in."}


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    await user_service.verify_email(db, token)
    return {"message": "Your e-mail address has been verified."}


@router.get("/me", response_model=UserAccountSchema)
async def get_my_account(current_user: User = Depends(get_current_user)):
    return user_service.serialize_user(current_user)


@router.patch("/me/profile", response_model=UserAccountSchema)
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = current_user.profile
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.flush()
    return user_service.serialize_user(current_user)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password and sign out every other session."""
    await user_service.change_password(db, current_user, payload.current_password, payload.new_password)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Deactivate and anonymise the caller's account (financial records are retained)."""
    await user_service.deactivate_account(db, current_user)
