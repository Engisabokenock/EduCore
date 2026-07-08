import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc
from app.core.database import get_db
from app.core.exceptions import AppBaseException, AuthorizationError
from app.api.deps import get_current_user, RoleChecker
from app.models.base import User, UserRole
from app.models.school import School, Classroom, ClassroomEnrollment, ClassAssignment, AssignmentSubmission, AssignmentStatus
from app.schemas.school import (
    SchoolCreateRequest, SchoolResponse, ClassroomCreateRequest,
    ClassroomResponse, AssignmentCreateRequest, AssignmentResponse, GradeAssignmentRequest
)

router = APIRouter(prefix="/schools", tags=["Institutional & Classroom Management Systems Engine"])

# Access Gateguards
admin_protect = Depends(RoleChecker([UserRole.ADMIN]))
teacher_protect = Depends(RoleChecker([UserRole.TEACHER]))

# --- SCHOOL REGISTRATION PATHWAYS ---

@router.post("", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED, dependencies=[admin_protect])
async def register_new_school(payload: SchoolCreateRequest, db: AsyncSession = Depends(get_db)):
    """Registers an institutional school root profile node inside the system matrix."""
    stmt = select(School).where(School.registration_code == payload.registration_code)
    if (await db.execute(stmt)).scalar_one_or_none():
        raise AppBaseException("Registration code token has already been occupied", 409)

    school = School(**payload.model_dump())
    db.add(school)
    await db.flush()
    return school

# --- CLASSROOM & STREAM STREAMLINING ---

@router.post("/{school_id}/classrooms", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED, dependencies=[admin_protect])
async def create_school_classroom(school_id: uuid.UUID, payload: ClassroomCreateRequest, db: AsyncSession = Depends(get_db)):
    """Creates a distinct class stream tracking container mapped inside an institutional branch."""
    classroom = Classroom(school_id=school_id, **payload.model_dump())
    db.add(classroom)
    try:
        await db.flush()
    except Exception:
        raise AppBaseException("Collision: Stream metadata details break consistency layout mappings", 400)
    return classroom

@router.post("/classrooms/{classroom_id}/enroll", status_code=status.HTTP_204_NO_CONTENT, dependencies=[admin_protect])
async def enroll_student_to_classroom(classroom_id: uuid.UUID, student_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Enrolls a student user identity container into a live classroom stream track."""
    enrollment = ClassroomEnrollment(classroom_id=classroom_id, student_id=student_id)
    db.add(enrollment)
    try:
        await db.flush()
    except Exception:
        raise AppBaseException("Student is already bound into this classroom tracking node", 400)

# --- ASSIGNMENT WORKFLOW ENGINES (TEACHER CONTROL GRID) ---

@router.post("/classrooms/{classroom_id}/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def issue_classroom_assignment(
    classroom_id: uuid.UUID,
    payload: AssignmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enables verified teachers to dispatch tasks and learning outcomes tests down to a classroom stream matrix."""
    if current_user.role.name != UserRole.TEACHER:
        raise AuthorizationError("Only Educators are cleared to broadcast coursework files parameters")

    assignment = ClassAssignment(
        classroom_id=classroom_id,
        teacher_id=current_user.id,
        **payload.model_dump()
    )
    db.add(assignment)
    await db.flush()
    return assignment

@router.post("/assignments/{assignment_id}/grade/{submission_id}", status_code=status.HTTP_200_OK, dependencies=[teacher_protect])
async def grade_student_submission(
    assignment_id: uuid.UUID,
    submission_id: uuid.UUID,
    payload: GradeAssignmentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Allows teachers to write scores, grading metrics, and structural text evaluations back to submissions."""
    stmt = select(AssignmentSubmission).where(AssignmentSubmission.id == submission_id)
    ctx = await db.execute(stmt)
    submission = ctx.scalar_one_or_none()

    if not submission or submission.assignment_id != assignment_id:
        raise AppBaseException("Submission file tracking node reference mismatch", 404)

    submission.score_achieved = payload.score_achieved
    submission.teacher_feedback = payload.teacher_feedback
    submission.status = AssignmentStatus.GRADED
    submission.graded_at = datetime.now(timezone.utc)

    db.add(submission)
    return {"status": "success", "message": "Grading parameter matrix entries locked and synced"}
