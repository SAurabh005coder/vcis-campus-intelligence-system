import React, { useEffect, useState } from "react";
import type { CourseInfo, DepartmentInfo } from "../../api/studentApi";
import {
  type CourseProposal,
  type SubjectProposal,
  createCourseProposal,
  createSubjectProposal,
  getCourseProposals,
  getSubjectProposals,
} from "../../api/proposalApi";

interface AcademicPlanningProps {
  departmentInfo: DepartmentInfo | null;
  courses: CourseInfo[];
}

export const AcademicPlanning: React.FC<AcademicPlanningProps> = ({
  departmentInfo,
  courses,
}) => {
  const [activeTab, setActiveTab] = useState<"courses" | "subjects">("courses");
  const [courseProposals, setCourseProposals] = useState<CourseProposal[]>([]);
  const [subjectProposals, setSubjectProposals] = useState<SubjectProposal[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modal States
  const [isCourseModalOpen, setIsCourseModalOpen] = useState(false);
  const [isSubjectModalOpen, setIsSubjectModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // New Course Form State
  const [courseName, setCourseName] = useState("");
  const [courseCode, setCourseCode] = useState("");
  const [durationYears, setDurationYears] = useState(2);
  const [totalSemesters, setTotalSemesters] = useState(4);
  const [courseDescription, setCourseDescription] = useState("");

  // New Subject Form State
  const [targetCourseId, setTargetCourseId] = useState<number | "">("");
  const [subjectName, setSubjectName] = useState("");
  const [subjectCode, setSubjectCode] = useState("");
  const [subjectSemester, setSubjectSemester] = useState(1);
  const [subjectCredits, setSubjectCredits] = useState(4);
  const [subjectDescription, setSubjectDescription] = useState("");

  const scopedCourses = departmentInfo
    ? courses.filter((c) => c.department_id === departmentInfo.id)
    : [];

  const loadProposals = async () => {
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
    loadProposals();
  }, []);

  const handleCreateCourseProposal = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccessMsg(null);

    try {
      await createCourseProposal({
        name: courseName.trim(),
        code: courseCode.trim().toUpperCase(),
        duration_years: Number(durationYears),
        total_semesters: Number(totalSemesters),
        description: courseDescription.trim() || null,
      });

      setSuccessMsg(`Course proposal "${courseCode.trim()}" submitted successfully.`);
      setIsCourseModalOpen(false);
      setCourseName("");
      setCourseCode("");
      setCourseDescription("");
      setDurationYears(2);
      setTotalSemesters(4);
      await loadProposals();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(e.response?.data?.detail || e.message || "Failed to submit course proposal.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateSubjectProposal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetCourseId) {
      setError("Please select a target course.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSuccessMsg(null);

    try {
      await createSubjectProposal({
        course_id: Number(targetCourseId),
        name: subjectName.trim(),
        code: subjectCode.trim().toUpperCase(),
        semester: Number(subjectSemester),
        credits: Number(subjectCredits),
        description: subjectDescription.trim() || null,
      });

      setSuccessMsg(`Subject proposal "${subjectCode.trim()}" submitted successfully.`);
      setIsSubjectModalOpen(false);
      setTargetCourseId("");
      setSubjectName("");
      setSubjectCode("");
      setSubjectDescription("");
      setSubjectSemester(1);
      setSubjectCredits(4);
      await loadProposals();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(e.response?.data?.detail || e.message || "Failed to submit subject proposal.");
    } finally {
      setIsSubmitting(false);
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

  const courseMap = new Map<number, string>();
  courses.forEach((c) => courseMap.set(c.id, `${c.name} (${c.code})`));

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)" }}>
      {/* Header */}
      <div className="vcis-card-header" style={{ flexWrap: "wrap", gap: "var(--space-4)" }}>
        <div>
          <h3 className="vcis-card-title">Academic Governance & Curriculum Planning</h3>
          <p className="vcis-card-subtitle">
            Department-scoped course & curriculum proposals submitted for institutional approval
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
          <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
            Authority Scope:{" "}
            <strong style={{ color: "var(--vcis-text)" }}>
              {departmentInfo ? `${departmentInfo.name} (${departmentInfo.code})` : "Department HOD"}
            </strong>
          </span>

          <button
            id="hod-propose-course-btn"
            onClick={() => {
              setError(null);
              setSuccessMsg(null);
              setIsCourseModalOpen(true);
            }}
            className="vcis-btn vcis-btn-primary"
            style={{ fontSize: "var(--vcis-font-size-xs)" }}
          >
            + Propose Course
          </button>

          <button
            id="hod-propose-subject-btn"
            onClick={() => {
              setError(null);
              setSuccessMsg(null);
              setIsSubjectModalOpen(true);
            }}
            className="vcis-btn vcis-btn-secondary"
            style={{ fontSize: "var(--vcis-font-size-xs)" }}
          >
            + Propose Subject
          </button>
        </div>
      </div>

      <div className="vcis-card-body">
        {/* Messages */}
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

        {/* Navigation Tabs */}
        <div style={{ display: "flex", gap: "var(--space-2)", borderBottom: "1px solid var(--vcis-border)", marginBottom: "var(--space-4)" }}>
          <button
            id="hod-tab-course-proposals"
            className={`vcis-btn ${activeTab === "courses" ? "vcis-btn-primary" : "vcis-btn-ghost"}`}
            style={{ borderRadius: "var(--radius-sm) var(--radius-sm) 0 0", borderBottom: activeTab === "courses" ? "2px solid var(--vcis-primary)" : "none" }}
            onClick={() => setActiveTab("courses")}
          >
            Course Proposals ({courseProposals.length})
          </button>
          <button
            id="hod-tab-subject-proposals"
            className={`vcis-btn ${activeTab === "subjects" ? "vcis-btn-primary" : "vcis-btn-ghost"}`}
            style={{ borderRadius: "var(--radius-sm) var(--radius-sm) 0 0", borderBottom: activeTab === "subjects" ? "2px solid var(--vcis-primary)" : "none" }}
            onClick={() => setActiveTab("subjects")}
          >
            Subject Proposals ({subjectProposals.length})
          </button>
        </div>

        {/* Tab 1: Course Proposals */}
        {activeTab === "courses" && (
          <div>
            {isLoading ? (
              <div style={{ padding: "var(--space-6)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
                Loading course proposals...
              </div>
            ) : courseProposals.length === 0 ? (
              <div style={{ padding: "var(--space-6)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
                No course proposals submitted yet for this department. Click <strong>+ Propose Course</strong> to submit one.
              </div>
            ) : (
              <div className="vcis-table-container">
                <table className="vcis-table">
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Course Name</th>
                      <th>Duration / Semesters</th>
                      <th>Status</th>
                      <th>Submission Date</th>
                      <th>Review Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {courseProposals.map((proposal) => (
                      <tr key={proposal.id}>
                        <td>
                          <strong>{proposal.code}</strong>
                        </td>
                        <td>{proposal.name}</td>
                        <td>
                          {proposal.duration_years} yr ({proposal.total_semesters} sems)
                        </td>
                        <td>{getStatusBadge(proposal.status)}</td>
                        <td>{new Date(proposal.created_at).toLocaleDateString()}</td>
                        <td>
                          {proposal.status === "REJECTED" && (
                            <div style={{ color: "var(--vcis-danger)", fontSize: "var(--vcis-font-size-xs)" }}>
                              <strong>Reason:</strong> {proposal.review_comment || "None provided"}
                            </div>
                          )}
                          {proposal.status === "APPROVED" && (
                            <div style={{ color: "var(--vcis-success)", fontSize: "var(--vcis-font-size-xs)" }}>
                              Official course created {proposal.review_comment ? `(${proposal.review_comment})` : ""}
                            </div>
                          )}
                          {proposal.status === "PENDING_APPROVAL" && (
                            <span style={{ color: "var(--vcis-text-muted)", fontSize: "var(--vcis-font-size-xs)" }}>
                              Awaiting Administrative Review
                            </span>
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
            ) : subjectProposals.length === 0 ? (
              <div style={{ padding: "var(--space-6)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
                No subject proposals submitted yet for this department. Click <strong>+ Propose Subject</strong> to submit one.
              </div>
            ) : (
              <div className="vcis-table-container">
                <table className="vcis-table">
                  <thead>
                    <tr>
                      <th>Subject Code</th>
                      <th>Subject Name</th>
                      <th>Target Course</th>
                      <th>Semester</th>
                      <th>Credits</th>
                      <th>Status</th>
                      <th>Review Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subjectProposals.map((proposal) => (
                      <tr key={proposal.id}>
                        <td>
                          <strong>{proposal.code}</strong>
                        </td>
                        <td>{proposal.name}</td>
                        <td>{courseMap.get(proposal.course_id) || `Course #${proposal.course_id}`}</td>
                        <td>Semester {proposal.semester}</td>
                        <td>{proposal.credits} cr</td>
                        <td>{getStatusBadge(proposal.status)}</td>
                        <td>
                          {proposal.status === "REJECTED" && (
                            <div style={{ color: "var(--vcis-danger)", fontSize: "var(--vcis-font-size-xs)" }}>
                              <strong>Reason:</strong> {proposal.review_comment || "None provided"}
                            </div>
                          )}
                          {proposal.status === "APPROVED" && (
                            <div style={{ color: "var(--vcis-success)", fontSize: "var(--vcis-font-size-xs)" }}>
                              Official subject created
                            </div>
                          )}
                          {proposal.status === "PENDING_APPROVAL" && (
                            <span style={{ color: "var(--vcis-text-muted)", fontSize: "var(--vcis-font-size-xs)" }}>
                              Awaiting Administrative Review
                            </span>
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
      </div>

      {/* Modal 1: Propose Course */}
      {isCourseModalOpen && (
        <div className="vcis-modal-backdrop" onClick={() => setIsCourseModalOpen(false)}>
          <div
            className="vcis-modal"
            style={{ maxWidth: "540px" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="vcis-modal-header">
              <h3 className="vcis-modal-title">Propose New Academic Course</h3>
              <button
                className="vcis-modal-close"
                onClick={() => setIsCourseModalOpen(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateCourseProposal}>
              <div className="vcis-modal-body" style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
                <div>
                  <label className="vcis-form-label">
                    Department Authority (Locked)
                  </label>
                  <input
                    type="text"
                    disabled
                    className="vcis-input"
                    value={departmentInfo ? `${departmentInfo.name} (${departmentInfo.code})` : "Current HOD Department"}
                    style={{ backgroundColor: "var(--vcis-surface-muted)", cursor: "not-allowed" }}
                  />
                </div>

                <div>
                  <label className="vcis-form-label" htmlFor="new-course-name">
                    Official Course Name *
                  </label>
                  <input
                    id="new-course-name"
                    type="text"
                    required
                    placeholder="e.g. M.Tech Artificial Intelligence"
                    className="vcis-input"
                    value={courseName}
                    onChange={(e) => setCourseName(e.target.value)}
                  />
                </div>

                <div>
                  <label className="vcis-form-label" htmlFor="new-course-code">
                    Course Code *
                  </label>
                  <input
                    id="new-course-code"
                    type="text"
                    required
                    placeholder="e.g. MTECH-AI"
                    className="vcis-input"
                    value={courseCode}
                    onChange={(e) => setCourseCode(e.target.value)}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-4)" }}>
                  <div>
                    <label className="vcis-form-label" htmlFor="new-course-duration">
                      Duration (Years) *
                    </label>
                    <input
                      id="new-course-duration"
                      type="number"
                      required
                      min={1}
                      max={6}
                      className="vcis-input"
                      value={durationYears}
                      onChange={(e) => setDurationYears(Number(e.target.value))}
                    />
                  </div>
                  <div>
                    <label className="vcis-form-label" htmlFor="new-course-semesters">
                      Total Semesters *
                    </label>
                    <input
                      id="new-course-semesters"
                      type="number"
                      required
                      min={1}
                      max={12}
                      className="vcis-input"
                      value={totalSemesters}
                      onChange={(e) => setTotalSemesters(Number(e.target.value))}
                    />
                  </div>
                </div>

                <div>
                  <label className="vcis-form-label" htmlFor="new-course-desc">
                    Curriculum Description (Optional)
                  </label>
                  <textarea
                    id="new-course-desc"
                    rows={3}
                    placeholder="Provide rationale, credit structure, and focus areas..."
                    className="vcis-textarea"
                    value={courseDescription}
                    onChange={(e) => setCourseDescription(e.target.value)}
                  />
                </div>
              </div>

              <div className="vcis-modal-footer">
                <button
                  type="button"
                  className="vcis-btn vcis-btn-ghost"
                  onClick={() => setIsCourseModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  id="submit-course-proposal-btn"
                  disabled={isSubmitting}
                  className="vcis-btn vcis-btn-primary"
                >
                  {isSubmitting ? "Submitting..." : "Submit Proposal for Approval"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 2: Propose Subject */}
      {isSubjectModalOpen && (
        <div className="vcis-modal-backdrop" onClick={() => setIsSubjectModalOpen(false)}>
          <div
            className="vcis-modal"
            style={{ maxWidth: "540px" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="vcis-modal-header">
              <h3 className="vcis-modal-title">Propose New Academic Subject</h3>
              <button
                className="vcis-modal-close"
                onClick={() => setIsSubjectModalOpen(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSubjectProposal}>
              <div className="vcis-modal-body" style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
                <div>
                  <label className="vcis-form-label" htmlFor="new-subject-course">
                    Target Course (Department Scoped) *
                  </label>
                  <select
                    id="new-subject-course"
                    required
                    className="vcis-select"
                    value={targetCourseId}
                    onChange={(e) => setTargetCourseId(Number(e.target.value))}
                  >
                    <option value="">-- Select Active Department Course --</option>
                    {scopedCourses.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.code}) — {c.total_semesters} Semesters
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="vcis-form-label" htmlFor="new-subject-name">
                    Subject Name *
                  </label>
                  <input
                    id="new-subject-name"
                    type="text"
                    required
                    placeholder="e.g. Distributed Computing"
                    className="vcis-input"
                    value={subjectName}
                    onChange={(e) => setSubjectName(e.target.value)}
                  />
                </div>

                <div>
                  <label className="vcis-form-label" htmlFor="new-subject-code">
                    Subject Code *
                  </label>
                  <input
                    id="new-subject-code"
                    type="text"
                    required
                    placeholder="e.g. MCA-204"
                    className="vcis-input"
                    value={subjectCode}
                    onChange={(e) => setSubjectCode(e.target.value)}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-4)" }}>
                  <div>
                    <label className="vcis-form-label" htmlFor="new-subject-semester">
                      Semester Level *
                    </label>
                    <input
                      id="new-subject-semester"
                      type="number"
                      required
                      min={1}
                      max={12}
                      className="vcis-input"
                      value={subjectSemester}
                      onChange={(e) => setSubjectSemester(Number(e.target.value))}
                    />
                  </div>
                  <div>
                    <label className="vcis-form-label" htmlFor="new-subject-credits">
                      Credits *
                    </label>
                    <input
                      id="new-subject-credits"
                      type="number"
                      required
                      min={1}
                      max={10}
                      className="vcis-input"
                      value={subjectCredits}
                      onChange={(e) => setSubjectCredits(Number(e.target.value))}
                    />
                  </div>
                </div>

                <div>
                  <label className="vcis-form-label" htmlFor="new-subject-desc">
                    Curriculum Description (Optional)
                  </label>
                  <textarea
                    id="new-subject-desc"
                    rows={3}
                    placeholder="Course topics, modules, and assessment structure..."
                    className="vcis-textarea"
                    value={subjectDescription}
                    onChange={(e) => setSubjectDescription(e.target.value)}
                  />
                </div>
              </div>

              <div className="vcis-modal-footer">
                <button
                  type="button"
                  className="vcis-btn vcis-btn-ghost"
                  onClick={() => setIsSubjectModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  id="submit-subject-proposal-btn"
                  disabled={isSubmitting}
                  className="vcis-btn vcis-btn-primary"
                >
                  {isSubmitting ? "Submitting..." : "Submit Subject Proposal"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
