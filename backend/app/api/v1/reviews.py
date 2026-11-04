import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc
from app.core.database import get_db
from app.core.exceptions import AppBaseException, AuthorizationError
from app.api.deps import get_current_user, RoleChecker, is_staff
from app.models.base import User, UserRole
from app.models.resource import AcademicResource
from app.models.review import ResourceReview, ReviewModerationStatus
from app.schemas.review import ReviewCreateRequest, ReviewUpdateRequest, ReportAbuseRequest, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Asset Feedback & Review Moderation System Engine"])

# --- PUBLIC / LEARNER ENDPOINTS ---

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_resource_review(
    payload: ReviewCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submits a star rating and comment text entry block against a distinct educational content node."""
    # Check if a historical feedback row entry already binds these pairs
    resource_exists = await db.execute(
        select(AcademicResource.id).where(AcademicResource.id == payload.resource_id, AcademicResource.is_published.is_(True))
    )
    if not resource_exists.first():
        raise AppBaseException("Resource not found", 404)
    stmt = select(ResourceReview).where(
        and_(ResourceReview.user_id == current_user.id, ResourceReview.resource_id == payload.resource_id)
    )
    ctx = await db.execute(stmt)
    if ctx.scalar_one_or_none():
        raise AppBaseException("You have already recorded feedback metrics tracking against this asset node container", 409)

    review = ResourceReview(
        resource_id=payload.resource_id,
        user_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment,
        moderation_status=ReviewModerationStatus.PENDING # Defaults into moderation triage queues
    )
    db.add(review)
    await db.flush()
    return review

@router.get("/resource/{resource_id}", response_model=list[ReviewResponse])
async def list_approved_resource_reviews(
    resource_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves public, approved feedback components mapping against targeted items."""
    stmt = select(ResourceReview).where(
        and_(ResourceReview.resource_id == resource_id, ResourceReview.moderation_status == ReviewModerationStatus.APPROVED)
    ).order_by(desc(ResourceReview.created_at)).limit(limit).offset(offset)

    res = await db.execute(stmt)
    return res.scalars().all()

@router.patch("/{review_id}", response_model=ReviewResponse)
async def modify_user_review(
    review_id: uuid.UUID,
    payload: ReviewUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enables self-service corrections or parameter metric switches for original submission profiles."""
    stmt = select(ResourceReview).where(ResourceReview.id == review_id)
    ctx = await db.execute(stmt)
    review = ctx.scalar_one_or_none()

    if not review:
        raise AppBaseException("Target database feedback node matching id trace parameter missing", 404)
    if review.user_id != current_user.id:
        raise AuthorizationError("Identity parameters block authorization modifications on external feedback layers")

    if payload.rating is not None:
        review.rating = payload.rating
    if payload.comment is not None:
        review.comment = payload.comment

    # Reset tracking status parameters down to triage loops upon alterations
    review.moderation_status = ReviewModerationStatus.PENDING
    db.add(review)
    await db.flush()
    return review

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enables immediate self-deletion or programmatic administrative purging actions cascades."""
    stmt = select(ResourceReview).where(ResourceReview.id == review_id)
    ctx = await db.execute(stmt)
    review = ctx.scalar_one_or_none()

    if not review:
        raise AppBaseException("Feedback record allocation path block missing", 404)

    # Grant bypass privileges to structural system managers alongside original submission records owners
    if review.user_id != current_user.id and not is_staff(current_user):
        raise AuthorizationError("Insufficient security privilege clearances for execution operations")

    await db.delete(review)

@router.post("/{review_id}/report", status_code=status.HTTP_202_ACCEPTED)
async def report_review_abuse(
    review_id: uuid.UUID,
    payload: ReportAbuseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Flags a comment line block parameter for violating Terms of Service layers, prompting safety triage reviews."""
    stmt = select(ResourceReview).where(ResourceReview.id == review_id)
    ctx = await db.execute(stmt)
    review = ctx.scalar_one_or_none()

    if not review:
        raise AppBaseException("Target feedback trace reference not found", 404)

    review.is_reported = True
    review.report_reason = payload.reason
    db.add(review)

# --- SYSTEM MODERATION / ADMINISTRATIVE ENDPOINTS ---

@router.get("/admin/moderation-queue", response_model=list[ReviewResponse], dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def view_administrative_moderation_queue(
    reported_only: bool = Query(False),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Returns unhandled review streams or community-flagged items requiring compliance choices."""
    conditions = []
    if reported_only:
        conditions.append(ResourceReview.is_reported == True)
    else:
        conditions.append(ResourceReview.moderation_status == ReviewModerationStatus.PENDING)

    stmt = select(ResourceReview).where(and_(*conditions)).order_by(desc(ResourceReview.created_at)).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/{review_id}/approve", response_model=ReviewResponse, dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def administrative_approve_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clears pending content assets or reports, publishing comments to global tracking grids."""
    stmt = select(ResourceReview).where(ResourceReview.id == review_id)
    ctx = await db.execute(stmt)
    review = ctx.scalar_one_or_none()

    if not review:
        raise AppBaseException("Feedback trace match reference missing", 404)

    review.moderation_status = ReviewModerationStatus.APPROVED
    review.is_reported = False # Clear community flags cleanly upon resolution
    review.moderated_by_id = current_user.id
    review.moderated_at = datetime.now(timezone.utc)

    db.add(review)
    await db.flush()
    return review

@router.post("/{review_id}/reject", response_model=ReviewResponse, dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def administrative_reject_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hides violating texts or ratings permanently, removing records from search indexing feeds."""
    stmt = select(ResourceReview).where(ResourceReview.id == review_id)
    ctx = await db.execute(stmt)
    review = ctx.scalar_one_or_none()

    if not review:
         raise AppBaseException("Feedback trace match reference missing", 404)

    review.moderation_status = ReviewModerationStatus.REJECTED
    review.moderated_by_id = current_user.id
    review.moderated_at = datetime.now(timezone.utc)

    db.add(review)
    await db.flush()
    return review
