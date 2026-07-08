import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.core.exceptions import AppBaseException, AuthenticationError
from app.core.email import AsyncEmailEngine
from app.models.base import User, Profile
from app.api.deps import get_current_user
from app.schemas.users import (
    ForgotPasswordRequest, ResetPasswordRequest, ProfileUpdateRequest,
    ChangePasswordRequest, UserAccountSchema
)

router = APIRouter(prefix="/users", tags=["Self-Service & Profile Management Engine"])

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == payload.email))
    user = res.scalar_one_or_none()
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.add(user)
        await AsyncEmailEngine.send_password_reset_email(user.email, token)

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(User).where(
            User.reset_token == payload.token,
            User.reset_token_expires > datetime.now(timezone.utc)
        )
    )
    user = res.scalar_one_or_none()
    if not user:
        raise AppBaseException("Reset token is invalid or has expired", status.HTTP_400_BAD_REQUEST)

    user.hashed_password = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.add(user)

@router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.verification_token == token))
    user = res.scalar_one_or_none()
    if not user:
        raise AppBaseException("Invalid email verification token supplied", status.HTTP_400_BAD_REQUEST)

    user.is_verified = True
    user.verification_token = None
    db.add(user)

@router.get("/me", response_model=UserAccountSchema)
async def get_my_account(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me/profile", response_model=UserAccountSchema)
async def update_profile(payload: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = current_user.profile
    if payload.full_name is not None:
        profile.full_name = payload.full_name
    if payload.phone_number is not None:
        profile.phone_number = payload.phone_number
    if payload.avatar_url is not None:
        profile.avatar_url = payload.avatar_url

    db.add(profile)
    await db.flush()
    return current_user

@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(payload: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise AuthenticationError("Current password validation signature failed")

    current_user.hashed_password = hash_password(payload.new_password)
    db.add(current_user)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Perform a cascade delete of the authenticated user
    await db.delete(current_user)
