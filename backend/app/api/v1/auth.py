import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_jwt_token, verify_jwt_token
from app.core.config import settings
from app.core.exceptions import AppBaseException, AuthenticationError
from app.core.email import AsyncEmailEngine
from app.api.deps import get_current_user
from app.models.base import User, Role, Profile, UserSession, UserRole
from app.schemas.users import RegistrationRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.auth import (
    UserLogin, TokenResponse, UserOut,
    AuthResultSchema, AuthTokensSchema, UserPublicSchema, RefreshRequest,
)

router = APIRouter(prefix="/auth", tags=["Identity Lifecycle Engine"])


def _user_public(user: User) -> dict:
    """Serialize a User ORM row into the frontend's expected User shape."""
    profile = getattr(user, "profile", None)
    full_name = profile.full_name if profile else ""
    parts = full_name.split(" ", 1)
    role = getattr(user, "role", None)
    return {
        "id": user.id,
        "email": user.email,
        "first_name": parts[0],
        "last_name": parts[1] if len(parts) > 1 else "",
        "full_name": full_name,
        "phone": profile.phone_number or "" if profile else "",
        "role": role.name if role else "student",
        "is_verified": user.is_verified,
        "date_joined": user.created_at.isoformat() if user.created_at else "",
        "profile": None,
    }


@router.post("/register", response_model=AuthResultSchema, status_code=status.HTTP_201_CREATED)
async def register(payload: RegistrationRequest, db: AsyncSession = Depends(get_db)):
    # Check uniqueness
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise AppBaseException("Email identity space occupied", status.HTTP_409_CONFLICT)

    # Locate targeted domain Role
    role_res = await db.execute(select(Role).where(Role.name == payload.role))
    role_entity = role_res.scalar_one_or_none()
    if not role_entity:
        # Emergency automated production bootstrapping if migration seeding was skipped
        role_entity = Role(name=payload.role)
        db.add(role_entity)
        await db.flush()

    full_name = payload.full_name or f"{payload.first_name} {payload.last_name}".strip()
    verification_token = secrets.token_urlsafe(32)

    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role_id=role_entity.id,
        verification_token=verification_token,
        is_verified=False,
    )
    new_user.role = role_entity
    db.add(new_user)
    await db.flush()

    profile = Profile(user_id=new_user.id, full_name=full_name, phone_number=payload.phone)
    new_user.profile = profile
    db.add(profile)
    await db.flush()

    access = create_jwt_token(new_user.id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh = create_jwt_token(new_user.id, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), is_refresh=True)

    session_record = UserSession(
        user_id=new_user.id,
        refresh_token=refresh,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session_record)
    await db.flush()

    await AsyncEmailEngine.send_verification_email(new_user.email, verification_token)
    await db.commit()
    return {"tokens": {"access": access, "refresh": refresh}, "user": _user_public(new_user)}

@router.post("/login", response_model=AuthResultSchema)
async def login(payload: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise AuthenticationError("Invalid structural verification parameters")

    access = create_jwt_token(user.id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh = create_jwt_token(user.id, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), is_refresh=True)

    # Persist the login session
    session_record = UserSession(
        user_id=user.id,
        refresh_token=refresh,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session_record)

    return {"tokens": {"access": access, "refresh": refresh}, "user": _user_public(user)}

@router.post("/refresh", response_model=AuthTokensSchema)
@router.post("/token/refresh", response_model=AuthTokensSchema)
async def refresh_tokens(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token = payload.refresh
    jwt_payload = verify_jwt_token(token, is_refresh=True)
    user_id = jwt_payload.get("sub")

    # Validate session storage row state
    session_res = await db.execute(
        select(UserSession).where(
            UserSession.refresh_token == token,
            UserSession.is_revoked == False
        )
    )
    session = session_res.scalar_one_or_none()
    if not session or session.expires_at < datetime.now(timezone.utc):
        raise AuthenticationError("Stale, compromised, or dropped active session contexts")

    # Rotate refresh tokens
    new_access = create_jwt_token(user_id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    new_refresh = create_jwt_token(user_id, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), is_refresh=True)

    session.is_revoked = True # Revoke the used token
    db.add(session)

    new_session = UserSession(
        user_id=UUID(user_id),
        refresh_token=new_refresh,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(new_session)

    return {"access": new_access, "refresh": new_refresh}

@router.get("/me", response_model=UserPublicSchema)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return _user_public(current_user)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(refresh_token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSession).where(UserSession.refresh_token == refresh_token))
    session = result.scalar_one_or_none()
    if session:
        session.is_revoked = True
        db.add(session)
