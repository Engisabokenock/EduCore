"""
Account application review.

Admins review teacher applications; only the Super Admin reviews administrator
applications. The rules live in ``app.services.approval_service``.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker
from app.core.database import get_db
from app.models.base import AccountApprovalStatus, User, UserRole
from app.schemas.approvals import ApplicationCounts, ApplicationOut, ApplicationPage, ReviewDecision
from app.services import approval_service

router = APIRouter(prefix="/admin-control-plane/approvals", tags=["Account Approvals"])

# Admins and the Super Admin (RoleChecker always admits SUPER_ADMIN). Which applications
# each of them may see and decide is enforced by the service.
reviewer = RoleChecker([UserRole.ADMIN])


@router.get("", response_model=ApplicationPage)
async def list_applications(
    status: AccountApprovalStatus = Query(AccountApprovalStatus.PENDING),
    role: Optional[UserRole] = Query(None, description="teacher or admin"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(reviewer),
    db: AsyncSession = Depends(get_db),
):
    return await approval_service.list_applications(
        db, current_user, status=status, role=role, page=page, page_size=page_size
    )


@router.get("/summary", response_model=ApplicationCounts)
async def pending_application_counts(
    current_user: User = Depends(reviewer), db: AsyncSession = Depends(get_db)
):
    return await approval_service.pending_counts(db, current_user)


@router.post("/{user_id}/approve", response_model=ApplicationOut)
async def approve_application(
    user_id: UUID,
    payload: Optional[ReviewDecision] = None,
    current_user: User = Depends(reviewer),
    db: AsyncSession = Depends(get_db),
):
    return await approval_service.approve(db, current_user, user_id, payload.note if payload else None)


@router.post("/{user_id}/reject", response_model=ApplicationOut)
async def reject_application(
    user_id: UUID,
    payload: Optional[ReviewDecision] = None,
    current_user: User = Depends(reviewer),
    db: AsyncSession = Depends(get_db),
):
    return await approval_service.reject(db, current_user, user_id, payload.note if payload else None)
