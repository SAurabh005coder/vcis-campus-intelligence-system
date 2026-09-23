import React, { useEffect, useState } from "react";
import type { CourseInfo, DepartmentInfo } from "../../api/studentApi";
import {
  type CourseProposal,
  type SubjectProposal,
  approveCourseProposal,
  approveSubjectProposal,
  getCourseProposals,
  getSubjectProposals,
  rejectCourseProposal,
  rejectSubjectProposal,
} from "../../api/proposalApi";

interface AdminProposalManagementProps {
  departments: DepartmentInfo[];
  courses: CourseInfo[];
  onProposalApproved?: () => void;
}

export const AdminProposalManagement: React.FC<AdminProposalManagementProps> = ({
  departments,
  courses,
  onProposalApproved,
}) => {
  const [activeTab, setActiveTab] = useState<"courses" | "subjects">("courses");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [deptFilter, setDeptFilter] = useState<number | "all">("all");

  const [courseProposals, setCourseProposals] = useState<CourseProposal[]>([]);
  const [subjectProposals, setSubjectProposals] = useState<SubjectProposal[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Review Modal State
  const [reviewModal, setReviewModal] = useState<{
    isOpen: boolean;
    type: "course" | "subject";
    action: "approve" | "reject";
    proposal: CourseProposal | SubjectProposal | null;
  }>({
    isOpen: false,
    type: "course",
    action: "approve",
    proposal: null,
  });

  const [reviewComment, setReviewComment] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const loadAllProposals = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [coursesData, subjectsData] = await Promise.all([
        getCourseProposals().catch(() => []),
        getSubjectProposals().catch(() => []),
      ]);
      setCourseProposals(coursesData);
      setSubjectProposals(subjectsData);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(e.response?.data?.detail || e.message || "Failed to load academic proposals.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllProposals();
  }, []);

  const deptMap = new Map<number, string>();
  departments.forEach((d) => deptMap.set(d.id, `${d.name} (${d.code})`));

  const courseMap = new Map<number, CourseInfo>();
  courses.forEach((c) => courseMap.set(c.id, c));

  const handleOpenReview = (
    type: "course" | "subject",
    action: "approve" | "reject",
    proposal: CourseProposal | SubjectProposal
  ) => {
    setError(null);
    setSuccessMsg(null);
    setReviewComment("");
    setReviewModal({
      isOpen: true,
      type,
      action,
      proposal,
    });
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewModal.proposal) return;

    if (reviewModal.action === "reject" && !reviewComment.trim()) {
      setError("Rejection requires a mandatory review reason.");
      return;
    }

    setIsProcessing(true);
    setError(null);
    setSuccessMsg(null);

    try {
      if (reviewModal.type === "course") {
        if (reviewModal.action === "approve") {
          await approveCourseProposal(reviewModal.proposal.id, reviewComment.trim() || undefined);
          setSuccessMsg(`Course proposal "${reviewModal.proposal.code}" approved successfully. Official course created.`);
          if (onProposalApproved) onProposalApproved();
        } else {
          await rejectCourseProposal(reviewModal.proposal.id, reviewComment.trim());
          setSuccessMsg(`Course proposal "${reviewModal.proposal.code}" has been rejected.`);
        }
      } else {
        if (reviewModal.action === "approve") {
          await approveSubjectProposal(reviewModal.proposal.id, reviewComment.trim() || undefined);
          setSuccessMsg(`Subject proposal "${reviewModal.proposal.code}" approved successfully. Official subject created.`);
          if (onProposalApproved) onProposalApproved();
        } else {
          await rejectSubjectProposal(reviewModal.proposal.id, reviewComment.trim());
          setSuccessMsg(`Subject proposal "${reviewModal.proposal.code}" has been rejected.`);
        }
      }

      setReviewModal({ isOpen: false, type: "course", action: "approve", proposal: null });
      setReviewComment("");
      await loadAllProposals();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(e.response?.data?.detail || e.message || "Failed to process proposal review.");
    } finally {
      setIsProcessing(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return <span className="vcis-badge vcis-badge-success">APPROVED</span>;
      case "REJECTED":
        return <span className="vcis-badge vcis-badge-danger">REJECTED</span>;
      case "PENDING_APPROVAL":
      default:
        return <span className="vcis-badge vcis-badge-warning">PENDING APPROVAL</span>;
    }
  };

  // Filtered Course Proposals
  const filteredCourseProposals = courseProposals.filter((p) => {
    const matchStatus = statusFilter === "all" || p.status === statusFilter;
    const matchDept = deptFilter === "all" || p.department_id === deptFilter;
    return matchStatus && matchDept;
  });

  // Filtered Subject Proposals
  const filteredSubjectProposals = subjectProposals.filter((p) => {
    const matchStatus = statusFilter === "all" || p.status === statusFilter;
    const targetCourse = courseMap.get(p.course_id);
    const matchDept =
      deptFilter === "all" || (targetCourse && targetCourse.department_id === deptFilter);
    return matchStatus && matchDept;
  });

  const pendingCourseCount = courseProposals.filter((p) => p.status === "PENDING_APPROVAL").length;
  const pendingSubjectCount = subjectProposals.filter((p) => p.status === "PENDING_APPROVAL").length;

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)" }}>
      {/* Header */}
      <div className="vcis-card-header" style={{ flexWrap: "wrap", gap: "var(--space-4)" }}>
        <div>
          <h3 className="vcis-card-title">Academic Governance & Curriculum Proposals</h3>
          <p className="vcis-card-subtitle">
            Review, approve, or reject department-level course and subject curriculum submissions
          </p>
        </div>

        {/* Global Filters */}
        <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap" }}>
          <div>
            <select
              id="admin-proposal-dept-filter"
              value={deptFilter}
              onChange={(e) =>
                setDeptFilter(e.target.value === "all" ? "all" : Number(e.target.value))
              }
              className="vcis-select"
              style={{ fontSize: "var(--vcis-font-size-xs)", minWidth: "180px" }}
            >
              <option value="all">All Departments ({departments.length})</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <select
              id="admin-proposal-status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="vcis-select"
              style={{ fontSize: "var(--vcis-font-size-xs)", minWidth: "160px" }}
            >
              <option value="all">All Statuses</option>
              <option value="PENDING_APPROVAL">Pending Approval</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      <div className="vcis-card-body">
        {/* Alerts */}
        {error && (
          <div
            className="vcis-alert vcis-alert-danger"
            style={{ marginBottom: "var(--space-4)", display: "flex", justifyContent: "space-between" }}
          >
            <span>{error}</span>
            <button onClick={() => setError(null)} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button>
          </div>
        )}

        {successMsg && (
          <div
            className="vcis-alert vcis-alert-success"
            style={{ marginBottom: "var(--space-4)", display: "flex", justifyContent: "space-between" }}
          >
            <span>{successMsg}</span>
            <button onClick={() => setSuccessMsg(null)} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button>
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: "flex", gap: "var(--space-2)", borderBottom: "1px solid var(--vcis-border)", marginBottom: "var(--space-4)" }}>
          <button
            id="admin-tab-course-proposals"
            className={`vcis-btn ${activeTab === "courses" ? "vcis-btn-primary" : "vcis-btn-ghost"}`}
            style={{ borderRadius: "var(--radius-sm) var(--radius-sm) 0 0", borderBottom: activeTab === "courses" ? "2px solid var(--vcis-primary)" : "none" }}
            onClick={() => setActiveTab("courses")}
          >
            Course Proposals ({filteredCourseProposals.length})
            {pendingCourseCount > 0 && (
              <span className="vcis-badge vcis-badge-warning" style={{ marginLeft: "var(--space-2)", fontSize: "0.7rem" }}>
                {pendingCourseCount} pending
              </span>
            )}
          </button>
          <button
            id="admin-tab-subject-proposals"
            className={`vcis-btn ${activeTab === "subjects" ? "vcis-btn-primary" : "vcis-btn-ghost"}`}
            style={{ borderRadius: "var(--radius-sm) var(--radius-sm) 0 0", borderBottom: activeTab === "subjects" ? "2px solid var(--vcis-primary)" : "none" }}
            onClick={() => setActiveTab("subjects")}
          >
            Subject Proposals ({filteredSubjectProposals.length})
            {pendingSubjectCount > 0 && (
              <span className="vcis-badge vcis-badge-warning" style={{ marginLeft: "var(--space-2)", fontSize: "0.7rem" }}>
                {pendingSubjectCount} pending
              </span>
            )}
          </button>
        </div>

        {/* Tab 1: Course Proposals */}
        {activeTab === "courses" && (
          <div>
            {isLoading ? (
              <div style={{ padding: "var(--space-6)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
                Loading course proposals...
              </div>
            ) : filteredCourseProposals.length === 0 ? (
              <div style={{ padding: "var(--space-6)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
                No course proposals found matching the selected filters.
              </div>
            ) : (
              <div className="vcis-table-container">
                <table className="vcis-table">
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Course Name</th>
                      <th>Department</th>
                      <th>Duration</th>
                      <th>Status</th>
                      <th>Submission Date</th>
                      <th>Audit / Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCourseProposals.map((proposal) => (
                      <tr key={proposal.id}>
                        <td>
                          <strong>{proposal.code}</strong>
                        </td>
                        <td>{proposal.name}</td>
                        <td>{deptMap.get(proposal.department_id) || `Dept #${proposal.department_id}`}</td>
                        <td>
                          {proposal.duration_years} yr ({proposal.total_semesters} sems)
                        </td>
                        <td>{getStatusBadge(proposal.status)}</td>
                        <td>{new Date(proposal.created_at).toLocaleDateString()}</td>
                        <td>
                          {proposal.status === "PENDING_APPROVAL" ? (
                            <div style={{ display: "flex", gap: "var(--space-2)" }}>
                              <button
                                id={`approve-course-prop-${proposal.id}`}
                                className="vcis-btn vcis-btn-primary"
                                style={{ fontSize: "0.75rem", padding: "var(--space-1) var(--space-2)" }}
                                onClick={() => handleOpenReview("course", "approve", proposal)}
                              >
                                Approve
                              </button>
                              <button
                                id={`reject-course-prop-${proposal.id}`}
                                className="vcis-btn vcis-btn-danger"
                                style={{ fontSize: "0.75rem", padding: "var(--space-1) var(--space-2)" }}
                                onClick={() => handleOpenReview("course", "reject", proposal)}
                              >
                                Reject
                              </button>
                            </div>
                          ) : (
                            <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
                              {proposal.status === "APPROVED" && (
                                <span style={{ color: "var(--vcis-success)" }}>
                                  ✓ Approved {proposal.reviewed_at ? `on ${new Date(proposal.reviewed_at).toLocaleDateString()}` : ""}
                                </span>
                              )}
                              {proposal.status === "REJECTED" && (
                                <span style={{ color: "var(--vcis-danger)" }}>
                                  ✕ Rejected: {proposal.review_comment}
                                </span>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Subject Proposals */}
        {activeTab === "subjects" && (
          <div>
            {isLoading ? (
              <div style={{ padding: "var(--space-6)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
                Loading subject proposals...
              </div>
            ) : filteredSubjectProposals.length === 0 ? (
              <div style={{ padding: "var(--space-6)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
                No subject proposals found matching the selected filters.
              </div>
            ) : (
              <div className="vcis-table-container">
                <table className="vcis-table">
                  <thead>
                    <tr>
                      <th>Subject Code</th>
                      <th>Subject Name</th>
                      <th>Course</th>
                      <th>Semester</th>
                      <th>Credits</th>
                      <th>Status</th>
                      <th>Audit / Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSubjectProposals.map((proposal) => {
                      const course = courseMap.get(proposal.course_id);
                      return (
                        <tr key={proposal.id}>
                          <td>
                            <strong>{proposal.code}</strong>
                          </td>
                          <td>{proposal.name}</td>
                          <td>{course ? `${course.name} (${course.code})` : `Course #${proposal.course_id}`}</td>
                          <td>Sem {proposal.semester}</td>
                          <td>{proposal.credits} cr</td>
                          <td>{getStatusBadge(proposal.status)}</td>
                          <td>
                            {proposal.status === "PENDING_APPROVAL" ? (
                              <div style={{ display: "flex", gap: "var(--space-2)" }}>
                                <button
                                  id={`approve-subject-prop-${proposal.id}`}
                                  className="vcis-btn vcis-btn-primary"
                                  style={{ fontSize: "0.75rem", padding: "var(--space-1) var(--space-2)" }}
                                  onClick={() => handleOpenReview("subject", "approve", proposal)}
                                >
                                  Approve
                                </button>
                                <button
                                  id={`reject-subject-prop-${proposal.id}`}
                                  className="vcis-btn vcis-btn-danger"
                                  style={{ fontSize: "0.75rem", padding: "var(--space-1) var(--space-2)" }}
                                  onClick={() => handleOpenReview("subject", "reject", proposal)}
                                >
                                  Reject
                                </button>
                              </div>
                            ) : (
                              <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
                                {proposal.status === "APPROVED" && (
                                  <span style={{ color: "var(--vcis-success)" }}>
                                    ✓ Approved {proposal.reviewed_at ? `on ${new Date(proposal.reviewed_at).toLocaleDateString()}` : ""}
                                  </span>
                                )}
                                {proposal.status === "REJECTED" && (
                                  <span style={{ color: "var(--vcis-danger)" }}>
                                    ✕ Rejected: {proposal.review_comment}
                                  </span>
                                )}
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Review Modal (Approve / Reject) */}
      {reviewModal.isOpen && reviewModal.proposal && (
        <div className="vcis-modal-backdrop" onClick={() => setReviewModal({ ...reviewModal, isOpen: false })}>
          <div
            className="vcis-modal"
            style={{ maxWidth: "500px" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="vcis-modal-header">
              <h3 className="vcis-modal-title">
                {reviewModal.action === "approve" ? "Approve Academic Proposal" : "Reject Academic Proposal"}
              </h3>
              <button
                className="vcis-modal-close"
                onClick={() => setReviewModal({ ...reviewModal, isOpen: false })}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmitReview}>
              <div className="vcis-modal-body" style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
                <div style={{ padding: "var(--space-3)", backgroundColor: "var(--vcis-surface-soft)", borderRadius: "var(--radius-sm)" }}>
                  <p style={{ margin: 0, fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
                    Target Proposal:
                  </p>
                  <p style={{ margin: "var(--space-1) 0 0 0", fontWeight: "var(--vcis-font-weight-semibold)", color: "var(--vcis-text)" }}>
                    {reviewModal.proposal.code} — {reviewModal.proposal.name}
                  </p>
                </div>

                {reviewModal.action === "approve" ? (
                  <p style={{ margin: 0, fontSize: "var(--vcis-font-size-sm)", color: "var(--vcis-text)" }}>
                    Approving this proposal will transactionally create the official curriculum record in the active academic catalog.
                  </p>
                ) : (
                  <p style={{ margin: 0, fontSize: "var(--vcis-font-size-sm)", color: "var(--vcis-danger)" }}>
                    Rejecting this proposal will preserve it in the permanent audit history. Please specify a clear administrative reason for the Department HOD:
                  </p>
                )}

                <div>
                  <label className="vcis-form-label" htmlFor="proposal-review-comment">
                    {reviewModal.action === "reject" ? "Reason for Rejection *" : "Administrative Comment (Optional)"}
                  </label>
                  <textarea
                    id="proposal-review-comment"
                    rows={3}
                    required={reviewModal.action === "reject"}
                    placeholder={
                      reviewModal.action === "reject"
                        ? "State the reason (e.g. curriculum overlap, credit guideline non-compliance)..."
                        : "Optional administrative approval note..."
                    }
                    className="vcis-textarea"
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                  />
                </div>
              </div>

              <div className="vcis-modal-footer">
                <button
                  type="button"
                  className="vcis-btn vcis-btn-ghost"
                  onClick={() => setReviewModal({ ...reviewModal, isOpen: false })}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  id="confirm-proposal-review-btn"
                  disabled={isProcessing}
                  className={`vcis-btn ${reviewModal.action === "approve" ? "vcis-btn-primary" : "vcis-btn-danger"}`}
                >
                  {isProcessing
                    ? "Processing..."
                    : reviewModal.action === "approve"
                    ? "Confirm Approval"
                    : "Confirm Rejection"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
