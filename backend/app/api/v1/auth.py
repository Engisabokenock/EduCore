from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import auth_rate_limiter, get_current_user
from app.core.database import get_db
from app.core.network import get_client_ip, get_user_agent
from app.models.base import User
from app.schemas.auth import AuthResultSchema, AuthTokensSchema, RefreshRequest, UserLogin, UserPublicSchema
from app.schemas.users import RegistrationRequest
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Identity Lifecycle Engine"])


@router.post(
    "/register", response_model=AuthResultSchema, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_rate_limiter)],
)
async def register(payload: RegistrationRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Create a student, teacher or parent account and sign the user in."""
    full_name = (payload.full_name or f"{payload.first_name} {payload.last_name}").strip()
    return await user_service.register_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=full_name,
        phone=payload.phone,
        role=payload.role,
        user_agent=get_user_agent(request),
        ip=get_client_ip(request),
    )


@router.post("/login", response_model=AuthResultSchema, dependencies=[Depends(auth_rate_limiter)])
async def login(payload: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    return await user_service.authenticate(
        db, email=payload.email, password=payload.password,
        user_agent=get_user_agent(request), ip=get_client_ip(request),
    )


@router.post("/refresh", response_model=AuthTokensSchema)
@router.post("/token/refresh", response_model=AuthTokensSchema)
async def refresh_tokens(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Rotate the refresh token. The old token is revoked; replaying it revokes every session."""
    return await user_service.rotate_refresh_token(db, payload.refresh)


@router.get("/me", response_model=UserPublicSchema)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return user_service.serialize_user(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await user_service.logout(db, payload.refresh)
