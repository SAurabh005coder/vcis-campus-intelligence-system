from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.course_proposal import ProposalStatus


class CourseProposalCreate(BaseModel):
    name: str = Field(..., max_length=150, description="Official course name")
    code: str = Field(..., max_length=30, description="Unique course identifier code")
    description: str | None = Field(default=None, description="Course synopsis or details")
    duration_years: int = Field(..., gt=0, description="Duration in years")
    total_semesters: int = Field(..., gt=0, description="Total academic semesters")


class CourseProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    proposed_by: int
    name: str
    code: str
    description: str | None
    duration_years: int
    total_semesters: int
    status: ProposalStatus
    reviewed_by: int | None
    reviewed_at: datetime | None
    review_comment: str | None
    created_at: datetime
    updated_at: datetime


class SubjectProposalCreate(BaseModel):
    course_id: int = Field(..., description="Target official course ID")
    name: str = Field(..., max_length=150, description="Official subject name")
    code: str = Field(..., max_length=30, description="Unique subject code")
    semester: int = Field(..., gt=0, description="Semester level")
    credits: int = Field(..., gt=0, description="Credit weight")
    description: str | None = Field(default=None, description="Curriculum description")


class SubjectProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    proposed_by: int
    name: str
    code: str
    semester: int
    credits: int
    description: str | None
    status: ProposalStatus
    reviewed_by: int | None
    reviewed_at: datetime | None
    review_comment: str | None
    created_at: datetime
    updated_at: datetime


class ProposalRejectRequest(BaseModel):
    review_comment: str = Field(..., min_length=1, description="Mandatory reason for rejection")


class ProposalApproveRequest(BaseModel):
    review_comment: str | None = Field(default=None, description="Optional administrative comment upon approval")
