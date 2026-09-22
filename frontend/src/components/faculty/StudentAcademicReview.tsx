import React from "react";
import type { DepartmentInfo, StudentAcademicSummaryResponse, StudentProfile } from "../../api/studentApi";
import type { PredictionResponse } from "../../api/predictionApi";
import type { CourseInfo } from "../../api/facultyApi";

interface StudentAcademicReviewProps {
  student: StudentProfile;
  prediction: PredictionResponse | null;
  isLoading: boolean;
  course?: CourseInfo | null;
  department?: DepartmentInfo | null;
  academicSummary?: StudentAcademicSummaryResponse | null;
  isSummaryLoading?: boolean;
  onOpenAttendanceModal?: () => void;
  onOpenAssessmentModal?: () => void;
}

export const StudentAcademicReview: React.FC<StudentAcademicReviewProps> = ({
  student,
  prediction,
  isLoading,
  course,
  department,
  academicSummary,
  isSummaryLoading,
  onOpenAttendanceModal,
  onOpenAssessmentModal,
}) => {
  const formatPercentage = (val?: number | null) => {
    if (val === undefined || val === null || isNaN(val)) {
      return "Not available";
    }
    return `${val.toFixed(2)}%`;
  };

  const features = prediction?.features;

  return (
    <div className="vcis-card">
      {/* Student Identity Header */}
      <div className="vcis-card-header">
        <div>
          <div className="vcis-prediction-label" style={{ color: "var(--vcis-accent)" }}>
            Selected Student
          </div>
          <h3 className="vcis-card-title" style={{ marginTop: "0.25rem" }}>
            {student.name}
          </h3>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>
            Roll No: <strong style={{ color: "var(--vcis-text)" }}>{student.roll_number}</strong> • ID: #{student.id} • Current Semester: <strong style={{ color: "var(--vcis-primary-hover)" }}>Sem {student.current_semester}</strong>
          </p>
        </div>

        <div style={{ textAlign: "right" }}>
          <span
            className="vcis-status vcis-status-neutral"
            style={{ fontSize: "var(--font-xs)" }}
          >
            {course ? `${course.name} (${course.code})` : `Course #${student.course_id}`}
          </span>
          <div style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)", marginTop: "0.25rem" }}>
            {department ? department.name : `Department #${student.department_id}`}
          </div>
        </div>
      </div>

      <div className="vcis-card-body">
        {/* Actions & Dynamic Academic Performance */}
        <div style={{ marginBottom: "var(--space-6)" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "var(--space-3)",
              marginBottom: "var(--space-3)",
            }}
          >
            <h4
              style={{
                margin: 0,
                fontSize: "var(--font-sm)",
                fontWeight: "var(--font-weight-semibold)",
                color: "var(--vcis-text)",
              }}
            >
              Academic Performance & Entry
            </h4>

            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              {onOpenAttendanceModal && (
                <button
                  type="button"
                  onClick={onOpenAttendanceModal}
                  id="record-attendance-btn"
                  className="vcis-button vcis-button-secondary vcis-button-sm"
                  title="Record attendance session for enrolled subject"
                >
                  📅 Record Attendance
                </button>
              )}
              {onOpenAssessmentModal && (
                <button
                  type="button"
                  onClick={onOpenAssessmentModal}
                  id="record-assessment-btn"
                  className="vcis-button vcis-button-primary vcis-button-sm"
                  title="Record CT1 or Assignment marks for enrolled subject"
                >
                  📝 Record Assessment
                </button>
              )}
            </div>
          </div>

          {isSummaryLoading ? (
            <div className="vcis-loading" style={{ padding: "var(--space-6) 0" }}>
              <div className="vcis-spinner" aria-hidden="true" />
              <span style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)" }}>
                Loading verified academic results...
              </span>
            </div>
          ) : academicSummary ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
              {/* Summary Metrics */}
              <div className="vcis-grid vcis-grid-2">
                <div
                  style={{
                    backgroundColor: "var(--vcis-surface-raised)",
                    border: "1px solid var(--vcis-border)",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-4)",
                  }}
                >
                  <div style={{ fontSize: "var(--font-xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)", lineHeight: 1.15 }}>
                    {formatPercentage(academicSummary.overall_percentage)}
                  </div>
                  <div className="vcis-kpi-label" style={{ marginTop: "0.2rem" }}>Cumulative Performance</div>
                  <div className="vcis-kpi-context" style={{ marginTop: "var(--space-2)" }}>
                    {academicSummary.total_obtained_marks} / {academicSummary.total_max_marks} Total Marks
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: "var(--vcis-surface-raised)",
                    border: "1px solid var(--vcis-border)",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-4)",
                  }}
                >
                  <div style={{ fontSize: "var(--font-xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-accent)", lineHeight: 1.15 }}>
                    {academicSummary.total_subjects} Subjects
                  </div>
                  <div className="vcis-kpi-label" style={{ marginTop: "0.2rem" }}>Enrolled Courses</div>
                  <div className="vcis-kpi-context" style={{ marginTop: "var(--space-2)" }}>Active term curriculum</div>
                </div>
              </div>

              {/* Subject Breakdown Table */}
              {academicSummary.subjects && academicSummary.subjects.length > 0 && (
                <div className="vcis-table-wrapper" style={{ maxHeight: "220px", overflowY: "auto" }}>
                  <table className="vcis-table">
                    <thead>
                      <tr>
                        <th className="vcis-table-header">Subject</th>
                        <th className="vcis-table-header" style={{ textAlign: "center" }}>Sem</th>
                        <th className="vcis-table-header" style={{ textAlign: "right" }}>Marks</th>
                        <th className="vcis-table-header" style={{ textAlign: "center" }}>%</th>
                        <th className="vcis-table-header">Key Assessments</th>
                      </tr>
                    </thead>
                    <tbody>
                      {academicSummary.subjects.map((sub) => (
                        <tr key={sub.enrollment_id} className="vcis-table-row">
                          <td className="vcis-table-cell" style={{ fontWeight: "var(--font-weight-semibold)" }}>
                            {sub.subject_name || `Subject #${sub.subject_id}`}
                            {sub.subject_code && (
                              <span style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)", marginLeft: "var(--space-2)" }}>
                                ({sub.subject_code})
                              </span>
                            )}
                          </td>
                          <td className="vcis-table-cell" style={{ textAlign: "center", color: "var(--vcis-text-muted)" }}>
                            {sub.semester ? `Sem ${sub.semester}` : "-"}
                          </td>
                          <td className="vcis-table-cell" style={{ textAlign: "right", color: "var(--vcis-text-muted)" }}>
                            {sub.total_obtained_marks} / {sub.total_max_marks}
                          </td>
                          <td className="vcis-table-cell" style={{ textAlign: "center", fontWeight: "var(--font-weight-semibold)" }}>
                            {formatPercentage(sub.overall_percentage)}
                          </td>
                          <td className="vcis-table-cell">
                            {sub.assessments && sub.assessments.length > 0 ? (
                              <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-1)" }}>
                                {sub.assessments.map((a, idx) => {
                                  const isCt2 = a.assessment_type?.toLowerCase() === "cycle_test_2" || a.assessment_name?.toLowerCase().includes("ct2") || a.assessment_name?.toLowerCase().includes("ct-2");
                                  return (
                                    <span
                                      key={idx}
                                      style={{
                                        backgroundColor: isCt2 ? "var(--vcis-surface-raised)" : "var(--vcis-primary-soft)",
                                        color: isCt2 ? "var(--vcis-text-muted)" : "var(--vcis-primary-hover)",
                                        padding: "0.15rem 0.4rem",
                                        borderRadius: "var(--radius-sm)",
                                        fontSize: "0.68rem",
                                        border: isCt2 ? "1px dashed var(--vcis-border)" : "none",
                                      }}
                                      title={isCt2 ? "Cycle Test 2 is a later assessment and NOT an early prediction input" : a.assessment_name}
                                    >
                                      {a.assessment_name}: {a.obtained_marks}/{a.max_marks}
                                    </span>
                                  );
                                })}
                              </div>
                            ) : (
                              <span style={{ color: "var(--vcis-text-muted)", fontSize: "var(--font-xs)" }}>No records</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div className="vcis-empty">
              Academic summary calculation pending or student has not enrolled in subjects for the current term.
            </div>
          )}
        </div>

        {/* Extracted Early Academic Indicators */}
        <div>
          <h4
            style={{
              margin: "0 0 var(--space-3) 0",
              fontSize: "var(--font-sm)",
              fontWeight: "var(--font-weight-semibold)",
              color: "var(--vcis-text)",
            }}
          >
            Early Academic Indicators (Semester {student.current_semester})
          </h4>

          {isLoading ? (
            <div className="vcis-loading" style={{ padding: "var(--space-6) 0" }}>
              <div className="vcis-spinner" aria-hidden="true" />
              <span style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)" }}>
                Extracting academic features...
              </span>
            </div>
          ) : features ? (
            <div className="vcis-grid vcis-grid-3">
              <div
                style={{
                  backgroundColor: "var(--vcis-surface-raised)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-3)",
                }}
              >
                <div className="vcis-kpi-label">Current Attendance</div>
                <div style={{ fontSize: "var(--font-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)" }}>
                  {formatPercentage(features.current_attendance)}
                </div>
                <div className="vcis-kpi-context">Recorded term attendance</div>
              </div>

              <div
                style={{
                  backgroundColor: "var(--vcis-surface-raised)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-3)",
                }}
              >
                <div className="vcis-kpi-label">Assignment Average</div>
                <div style={{ fontSize: "var(--font-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)" }}>
                  {formatPercentage(features.current_assignment_average)}
                </div>
                <div className="vcis-kpi-context">Continuous coursework</div>
              </div>

              <div
                style={{
                  backgroundColor: "var(--vcis-surface-raised)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-3)",
                }}
              >
                <div className="vcis-kpi-label">CT-1 Average</div>
                <div style={{ fontSize: "var(--font-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)" }}>
                  {formatPercentage(features.current_ct1_average)}
                </div>
                <div className="vcis-kpi-context">Cycle test 1 milestone</div>
              </div>

              {student.current_semester > 1 && (
                <>
                  <div
                    style={{
                      backgroundColor: "var(--vcis-surface-raised)",
                      border: "1px dashed var(--vcis-border)",
                      borderRadius: "var(--radius-md)",
                      padding: "var(--space-3)",
                    }}
                  >
                    <div className="vcis-kpi-label">Prev Sem Score</div>
                    <div style={{ fontSize: "var(--font-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text-secondary)" }}>
                      {formatPercentage(features.previous_semester_score)}
                    </div>
                    <div className="vcis-kpi-context">Sem {student.current_semester - 1} final result</div>
                  </div>

                  <div
                    style={{
                      backgroundColor: "var(--vcis-surface-raised)",
                      border: "1px dashed var(--vcis-border)",
                      borderRadius: "var(--radius-md)",
                      padding: "var(--space-3)",
                    }}
                  >
                    <div className="vcis-kpi-label">Prev Sem Attendance</div>
                    <div style={{ fontSize: "var(--font-lg)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text-secondary)" }}>
                      {formatPercentage(features.previous_semester_attendance)}
                    </div>
                    <div className="vcis-kpi-context">Sem {student.current_semester - 1} attendance</div>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="vcis-empty">
              Click <strong>&quot;Generate Early Prediction&quot;</strong> to evaluate early academic indicators and forecast score.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentAcademicReview;
