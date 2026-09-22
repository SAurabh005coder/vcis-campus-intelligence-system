import React from "react";
import type { StudentAcademicSummaryResponse } from "../../api/studentApi";

interface AssessmentResultSectionProps {
  summary: StudentAcademicSummaryResponse | null;
  isLoading: boolean;
}

export const AssessmentResultSection: React.FC<AssessmentResultSectionProps> = ({
  summary,
  isLoading,
}) => {
  const formatPercentage = (val?: number | null) => {
    if (val === undefined || val === null || isNaN(val)) {
      return "N/A";
    }
    return `${val.toFixed(1)}%`;
  };

  return (
    <div className="vcis-card">
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Assessments & Continuous Evaluation</h3>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>
            Breakdown of continuous cycle tests, assignments, and term evaluations
          </p>
        </div>

        {summary && (
          <span
            className="vcis-status vcis-status-info"
            style={{ fontSize: "var(--font-xs)" }}
          >
            Verified Average: {formatPercentage(summary.overall_percentage)}
          </span>
        )}
      </div>

      <div className="vcis-card-body">
        {isLoading ? (
          <div className="vcis-loading" style={{ padding: "var(--space-6) 0" }}>
            <div className="vcis-spinner" aria-hidden="true" />
            <span style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)" }}>
              Evaluating assessment scores...
            </span>
          </div>
        ) : !summary || summary.subjects.length === 0 ? (
          <div className="vcis-empty">
            No continuous assessment or enrollment results recorded for this term yet.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
            {/* Term Summary Cards */}
            <div className="vcis-grid vcis-grid-3">
              <div
                style={{
                  backgroundColor: "var(--vcis-surface-raised)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-4)",
                }}
              >
                <div className="vcis-kpi-label">Cumulative Performance</div>
                <div style={{ fontSize: "var(--font-2xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)" }}>
                  {formatPercentage(summary.overall_percentage)}
                </div>
                <div className="vcis-kpi-context">Weighted across active subjects</div>
              </div>

              <div
                style={{
                  backgroundColor: "var(--vcis-surface-raised)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-4)",
                }}
              >
                <div className="vcis-kpi-label">Registered Courses</div>
                <div style={{ fontSize: "var(--font-2xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-accent)" }}>
                  {summary.total_subjects} Subjects
                </div>
                <div className="vcis-kpi-context">Current semester curriculum</div>
              </div>

              <div
                style={{
                  backgroundColor: "var(--vcis-surface-raised)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-4)",
                }}
              >
                <div className="vcis-kpi-label">Curriculum Credits</div>
                <div style={{ fontSize: "var(--font-2xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-primary-hover)" }}>
                  {summary.subjects.reduce((sum, s) => sum + (s.credits || 0), 0)} Credits
                </div>
                <div className="vcis-kpi-context">Institutional credit load</div>
              </div>
            </div>

            {/* Assessment Details per Subject */}
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "var(--space-3)",
                }}
              >
                <h4 style={{ margin: 0, fontSize: "var(--font-sm)", fontWeight: "var(--font-weight-semibold)", color: "var(--vcis-text)" }}>
                  Subject Assessment Breakdown
                </h4>
                <span style={{ fontSize: "var(--font-xs)", color: "var(--vcis-accent)", fontWeight: "var(--font-weight-medium)" }}>
                  ★ CT1 & Assignments are primary early prediction inputs
                </span>
              </div>

              <div className="vcis-table-wrapper">
                <table className="vcis-table">
                  <thead>
                    <tr>
                      <th className="vcis-table-header">Code</th>
                      <th className="vcis-table-header">Subject Name</th>
                      <th className="vcis-table-header" style={{ textAlign: "center" }}>Credits</th>
                      <th className="vcis-table-header" style={{ textAlign: "center" }}>CT1 Milestone</th>
                      <th className="vcis-table-header" style={{ textAlign: "center" }}>Continuous Assignments</th>
                      <th className="vcis-table-header" style={{ textAlign: "right" }}>Marks Obtained</th>
                      <th className="vcis-table-header" style={{ textAlign: "center" }}>Overall %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.subjects.map((sub) => {
                      const ct1Assessments = sub.assessments.filter((a) => a.assessment_type === "CT1");
                      const assignAssessments = sub.assessments.filter((a) => a.assessment_type === "ASSIGNMENT");

                      return (
                        <tr key={sub.enrollment_id} className="vcis-table-row">
                          <td className="vcis-table-cell" style={{ fontWeight: "var(--font-weight-semibold)" }}>
                            {sub.subject_code}
                          </td>
                          <td className="vcis-table-cell">{sub.subject_name}</td>
                          <td className="vcis-table-cell" style={{ textAlign: "center", color: "var(--vcis-text-muted)" }}>
                            {sub.credits}
                          </td>
                          <td className="vcis-table-cell" style={{ textAlign: "center" }}>
                            {ct1Assessments.length > 0 ? (
                              <span
                                style={{
                                  padding: "0.2rem 0.5rem",
                                  borderRadius: "var(--radius-sm)",
                                  backgroundColor: "var(--vcis-primary-soft)",
                                  color: "var(--vcis-primary-hover)",
                                  fontWeight: "var(--font-weight-semibold)",
                                  fontSize: "var(--font-xs)",
                                }}
                              >
                                {ct1Assessments.map((a) => `${a.obtained_marks}/${a.max_marks}`).join(", ")}
                              </span>
                            ) : (
                              <span style={{ color: "var(--vcis-text-muted)", fontSize: "var(--font-xs)" }}>
                                Pending
                              </span>
                            )}
                          </td>
                          <td className="vcis-table-cell" style={{ textAlign: "center" }}>
                            {assignAssessments.length > 0 ? (
                              <span
                                style={{
                                  padding: "0.2rem 0.5rem",
                                  borderRadius: "var(--radius-sm)",
                                  backgroundColor: "var(--vcis-accent-soft)",
                                  color: "var(--vcis-accent)",
                                  fontWeight: "var(--font-weight-semibold)",
                                  fontSize: "var(--font-xs)",
                                }}
                              >
                                {assignAssessments.map((a) => `${a.obtained_marks}/${a.max_marks}`).join(", ")}
                              </span>
                            ) : (
                              <span style={{ color: "var(--vcis-text-muted)", fontSize: "var(--font-xs)" }}>
                                Pending
                              </span>
                            )}
                          </td>
                          <td className="vcis-table-cell" style={{ textAlign: "right", color: "var(--vcis-text-muted)" }}>
                            {sub.total_obtained_marks} / {sub.total_max_marks}
                          </td>
                          <td className="vcis-table-cell" style={{ textAlign: "center", fontWeight: "var(--font-weight-semibold)", color: "var(--vcis-text)" }}>
                            {sub.overall_percentage.toFixed(1)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AssessmentResultSection;
