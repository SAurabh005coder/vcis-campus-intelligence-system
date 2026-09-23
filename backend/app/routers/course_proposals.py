from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import require_roles, resolve_hod_department_id
from app.database import get_db
from app.models.course import Course
from app.models.course_proposal import CourseProposal, ProposalStatus
from app.models.department import Department
from app.models.user import User, UserRole
from app.schemas.proposal import (
    CourseProposalCreate,
    CourseProposalResponse,
    ProposalApproveRequest,
    ProposalRejectRequest,
)

router = APIRouter(
    prefix="/api/v1/course-proposals",
    tags=["Course Proposals"],
)


@router.post(
    "/",
    response_model=CourseProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course_proposal(
    proposal_data: CourseProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.HOD)),
):
    """
    HOD-only endpoint to submit a course proposal.
    The department_id is strictly derived from the HOD's linked Faculty profile.
    Client-supplied department_id is never accepted or trusted.
    """
    department_id = resolve_hod_department_id(current_user, db)

    department = (
        db.query(Department)
        .filter(
            Department.id == department_id,
            Department.is_active.is_(True),
        )
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active department not found for this HOD.",
        )

    # Check for name/code conflict in official courses
    existing_course_name = (
        db.query(Course)
        .filter(Course.name == proposal_data.name)
        .first()
    )
    if existing_course_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An official course with this name already exists.",
        )

    existing_course_code = (
        db.query(Course)
        .filter(Course.code == proposal_data.code)
        .first()
    )
    if existing_course_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An official course with this code already exists.",
        )

    # Check for duplicate pending proposal
    existing_pending = (
        db.query(CourseProposal)
        .filter(
            CourseProposal.status == ProposalStatus.PENDING_APPROVAL,
            (CourseProposal.name == proposal_data.name) | (CourseProposal.code == proposal_data.code),
        )
        .first()
    )
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending course proposal with this name or code already exists.",
        )

    proposal = CourseProposal(
        department_id=department_id,
        proposed_by=current_user.id,
        name=proposal_data.name,
        code=proposal_data.code,
        description=proposal_data.description,
        duration_years=proposal_data.duration_years,
        total_semesters=proposal_data.total_semesters,
        status=ProposalStatus.PENDING_APPROVAL,
    )

    db.add(proposal)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Proposal conflicts with an existing record.",
        )

    db.refresh(proposal)
    return proposal


@router.get(
    "/",
    response_model=list[CourseProposalResponse],
)
def get_course_proposals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.HOD, UserRole.ADMIN)),
):
    """
    Get course proposals.
    - ADMIN: returns all proposals across all departments.
    - HOD: returns ONLY proposals from their own department.
    """
    if current_user.role == UserRole.ADMIN:
        return db.query(CourseProposal).order_by(CourseProposal.created_at.desc()).all()

    hod_dept_id = resolve_hod_department_id(current_user, db)
    return (
        db.query(CourseProposal)
        .filter(CourseProposal.department_id == hod_dept_id)
        .order_by(CourseProposal.created_at.desc())
        .all()
    )


@router.get(
    "/{proposal_id}",
    response_model=CourseProposalResponse,
)
def get_course_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.HOD, UserRole.ADMIN)),
):
    """
    Get a specific course proposal.
    Enforces strict IDOR protection: HOD can only view proposals from their own department.
    """
    proposal = (
        db.query(CourseProposal)
        .filter(CourseProposal.id == proposal_id)
        .first()
    )

    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course proposal not found.",
        )

    if current_user.role == UserRole.HOD:
        hod_dept_id = resolve_hod_department_id(current_user, db)
        if proposal.department_id != hod_dept_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view course proposals from another department.",
            )

    return proposal


@router.post(
    "/{proposal_id}/approve",
    response_model=CourseProposalResponse,
)
def approve_course_proposal(
    proposal_id: int,
    review_data: ProposalApproveRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    ADMIN-only: Approve a course proposal.
    Transactionally creates an official Course record and marks proposal APPROVED.
    """
    proposal = (
        db.query(CourseProposal)
        .filter(CourseProposal.id == proposal_id)
        .first()
    )

    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course proposal not found.",
        )

    if proposal.status != ProposalStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only proposals with PENDING_APPROVAL status can be approved. Current status: {proposal.status.value}",
        )

    # Re-validate department existence and active state
    department = (
        db.query(Department)
        .filter(
            Department.id == proposal.department_id,
            Department.is_active.is_(True),
        )
        .first()
    )
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Associated department is inactive or no longer exists.",
        )

    # Re-validate course name & code uniqueness
    existing_name = (
        db.query(Course)
        .filter(Course.name == proposal.name)
        .first()
    )
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An official course with this name already exists.",
        )

    existing_code = (
        db.query(Course)
        .filter(Course.code == proposal.code)
        .first()
    )
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An official course with this code already exists.",
        )

    # Transactional execution: create official Course + update proposal
    official_course = Course(
        department_id=proposal.department_id,
        name=proposal.name,
        code=proposal.code,
        description=proposal.description,
        duration_years=proposal.duration_years,
        total_semesters=proposal.total_semesters,
        is_active=True,
    )
    db.add(official_course)

    proposal.status = ProposalStatus.APPROVED
    proposal.reviewed_by = current_user.id
    proposal.reviewed_at = datetime.now(timezone.utc)
    if review_data and review_data.review_comment:
        proposal.review_comment = review_data.review_comment

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to create official course due to a database constraint conflict.",
        )

    db.refresh(proposal)
    return proposal


@router.post(
    "/{proposal_id}/reject",
    response_model=CourseProposalResponse,
)
def reject_course_proposal(
    proposal_id: int,
    review_data: ProposalRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    ADMIN-only: Reject a course proposal with mandatory reason.
    Preserves proposal as permanent audit history.
    """
    proposal = (
        db.query(CourseProposal)
        .filter(CourseProposal.id == proposal_id)
        .first()
    )

    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course proposal not found.",
        )

    if proposal.status != ProposalStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only proposals with PENDING_APPROVAL status can be rejected. Current status: {proposal.status.value}",
        )

    comment = review_data.review_comment.strip()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rejection review comment cannot be empty.",
        )

    proposal.status = ProposalStatus.REJECTED
    proposal.reviewed_by = current_user.id
    proposal.reviewed_at = datetime.now(timezone.utc)
    proposal.review_comment = comment

    db.commit()
    db.refresh(proposal)
    return proposal
