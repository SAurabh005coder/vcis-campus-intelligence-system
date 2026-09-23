from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import require_roles, resolve_hod_department_id
from app.database import get_db
from app.models.course import Course
from app.models.course_proposal import ProposalStatus
from app.models.subject import Subject
from app.models.subject_proposal import SubjectProposal
from app.models.user import User, UserRole
from app.schemas.proposal import (
    ProposalApproveRequest,
    ProposalRejectRequest,
    SubjectProposalCreate,
    SubjectProposalResponse,
)

router = APIRouter(
    prefix="/api/v1/subject-proposals",
    tags=["Subject Proposals"],
)


@router.post(
    "/",
    response_model=SubjectProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject_proposal(
    proposal_data: SubjectProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.HOD)),
):
    """
    HOD-only endpoint to submit a subject proposal.
    The HOD can only propose subjects for active courses belonging to their own department.
    """
    hod_department_id = resolve_hod_department_id(current_user, db)

    course = (
        db.query(Course)
        .filter(
            Course.id == proposal_data.course_id,
            Course.is_active.is_(True),
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active course not found.",
        )

    # Cross-department check: course must belong to HOD's department
    if course.department_id != hod_department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only propose subjects for courses within your own department.",
        )

    # Semester validity check
    if proposal_data.semester > course.total_semesters or proposal_data.semester < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposed semester ({proposal_data.semester}) exceeds total course semesters ({course.total_semesters}).",
        )

    # Check official subject code uniqueness
    existing_code = (
        db.query(Subject)
        .filter(Subject.code == proposal_data.code)
        .first()
    )
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An official subject with this code already exists.",
        )

    # Check official duplicate subject for course + semester + name
    existing_official = (
        db.query(Subject)
        .filter(
            Subject.course_id == proposal_data.course_id,
            Subject.semester == proposal_data.semester,
            Subject.name == proposal_data.name,
        )
        .first()
    )
    if existing_official:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This subject already exists for the course and semester.",
        )

    # Check duplicate in pending subject proposals
    existing_pending_code = (
        db.query(SubjectProposal)
        .filter(
            SubjectProposal.status == ProposalStatus.PENDING_APPROVAL,
            SubjectProposal.code == proposal_data.code,
        )
        .first()
    )
    if existing_pending_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending subject proposal with this code already exists.",
        )

    existing_pending_subject = (
        db.query(SubjectProposal)
        .filter(
            SubjectProposal.status == ProposalStatus.PENDING_APPROVAL,
            SubjectProposal.course_id == proposal_data.course_id,
            SubjectProposal.semester == proposal_data.semester,
            SubjectProposal.name == proposal_data.name,
        )
        .first()
    )
    if existing_pending_subject:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending subject proposal already exists for this course, semester, and name.",
        )

    proposal = SubjectProposal(
        course_id=proposal_data.course_id,
        proposed_by=current_user.id,
        name=proposal_data.name,
        code=proposal_data.code,
        semester=proposal_data.semester,
        credits=proposal_data.credits,
        description=proposal_data.description,
        status=ProposalStatus.PENDING_APPROVAL,
    )

    db.add(proposal)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subject proposal conflicts with an existing record.",
        )

    db.refresh(proposal)
    return proposal


@router.get(
    "/",
    response_model=list[SubjectProposalResponse],
)
def get_subject_proposals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.HOD, UserRole.ADMIN)),
):
    """
    Get subject proposals.
    - ADMIN: returns all subject proposals across all departments.
    - HOD: returns ONLY proposals for courses belonging to their own department.
    """
    if current_user.role == UserRole.ADMIN:
        return db.query(SubjectProposal).order_by(SubjectProposal.created_at.desc()).all()

    hod_dept_id = resolve_hod_department_id(current_user, db)
    return (
        db.query(SubjectProposal)
        .join(Course, SubjectProposal.course_id == Course.id)
        .filter(Course.department_id == hod_dept_id)
        .order_by(SubjectProposal.created_at.desc())
        .all()
    )


@router.get(
    "/{proposal_id}",
    response_model=SubjectProposalResponse,
)
def get_subject_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.HOD, UserRole.ADMIN)),
):
    """
    Get a specific subject proposal.
    Enforces strict IDOR protection: HOD can only view proposals for courses in their own department.
    """
    proposal = (
        db.query(SubjectProposal)
        .filter(SubjectProposal.id == proposal_id)
        .first()
    )

    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject proposal not found.",
        )

    if current_user.role == UserRole.HOD:
        hod_dept_id = resolve_hod_department_id(current_user, db)
        course = (
            db.query(Course)
            .filter(Course.id == proposal.course_id)
            .first()
        )
        if course is None or course.department_id != hod_dept_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view subject proposals from another department.",
            )

    return proposal


@router.post(
    "/{proposal_id}/approve",
    response_model=SubjectProposalResponse,
)
def approve_subject_proposal(
    proposal_id: int,
    review_data: ProposalApproveRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    ADMIN-only: Approve a subject proposal.
    Transactionally creates an official Subject record and marks proposal APPROVED.
    """
    proposal = (
        db.query(SubjectProposal)
        .filter(SubjectProposal.id == proposal_id)
        .first()
    )

    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject proposal not found.",
        )

    if proposal.status != ProposalStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only proposals with PENDING_APPROVAL status can be approved. Current status: {proposal.status.value}",
        )

    # Re-validate target course
    course = (
        db.query(Course)
        .filter(
            Course.id == proposal.course_id,
            Course.is_active.is_(True),
        )
        .first()
    )
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target course is inactive or does not exist.",
        )

    if proposal.semester > course.total_semesters or proposal.semester < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal semester ({proposal.semester}) exceeds course total semesters ({course.total_semesters}).",
        )

    # Re-validate subject code uniqueness
    existing_code = (
        db.query(Subject)
        .filter(Subject.code == proposal.code)
        .first()
    )
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An official subject with this code already exists.",
        )

    # Re-validate course + semester + name uniqueness
    existing_subject = (
        db.query(Subject)
        .filter(
            Subject.course_id == proposal.course_id,
            Subject.semester == proposal.semester,
            Subject.name == proposal.name,
        )
        .first()
    )
    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This subject already exists for the course and semester.",
        )

    # Transactional execution: create official Subject + update proposal
    official_subject = Subject(
        course_id=proposal.course_id,
        name=proposal.name,
        code=proposal.code,
        semester=proposal.semester,
        credits=proposal.credits,
        description=proposal.description,
        is_active=True,
    )
    db.add(official_subject)

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
            detail="Failed to create official subject due to a database constraint conflict.",
        )

    db.refresh(proposal)
    return proposal


@router.post(
    "/{proposal_id}/reject",
    response_model=SubjectProposalResponse,
)
def reject_subject_proposal(
    proposal_id: int,
    review_data: ProposalRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    ADMIN-only: Reject a subject proposal with mandatory reason.
    Preserves proposal as permanent audit history.
    """
    proposal = (
        db.query(SubjectProposal)
        .filter(SubjectProposal.id == proposal_id)
        .first()
    )

    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject proposal not found.",
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
