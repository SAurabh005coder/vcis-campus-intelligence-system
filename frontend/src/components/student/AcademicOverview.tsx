import React from "react";

interface AcademicOverviewProps {
  currentSemester: number;
  attendance?: number | null;
  assignmentAverage?: number | null;
  ct1Average?: number | null;
  previousSemesterScore?: number | null;
  previousSemesterAttendance?: number | null;
  isLoading?: boolean;
}

export const AcademicOverview: React.FC<AcademicOverviewProps> = ({
  currentSemester,
  attendance,
  assignmentAverage,
  ct1Average,
  previousSemesterScore,
  previousSemesterAttendance,
  isLoading,
}) => {
  const formatPercentage = (val?: number | null) => {
    if (val === undefined || val === null || isNaN(val)) {
      return "Not available";
    }
    return `${val.toFixed(2)}%`;
  };

  return (
    <div className="vcis-card">
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Current Academic Performance</h3>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>
            Current milestone indicators utilized for predictive risk assessment
          </p>
        </div>
        <span
          className="vcis-status vcis-status-neutral"
          style={{ fontSize: "var(--font-xs)" }}
        >
          Semester {currentSemester}
        </span>
      </div>

      <div className="vcis-card-body">
        {isLoading ? (
          <div className="vcis-loading" style={{ padding: "var(--space-6) 0" }}>
            <div className="vcis-spinner" aria-hidden="true" />
            <span style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)" }}>
              Loading academic performance indicators...
            </span>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
            {/* Metric Indicator Cards */}
            <div className="vcis-grid vcis-grid-3">
              <div
                style={{
                  backgroundColor: "var(--vcis-surface-raised)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-4)",
                }}
              >
                <div className="vcis-kpi-label">Current Attendance</div>
                <div style={{ fontSize: "var(--font-xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)" }}>
                  {formatPercentage(attendance)}
                </div>
                <div style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)", marginTop: "var(--space-1)" }}>
                  Current recorded attendance
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
                <div className="vcis-kpi-label">Continuous Assignments</div>
                <div style={{ fontSize: "var(--font-xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)" }}>
                  {formatPercentage(assignmentAverage)}
                </div>
                <div style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)", marginTop: "var(--space-1)" }}>
                  Internal coursework average
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
                <div className="vcis-kpi-label">Cycle Test 1 (CT1)</div>
                <div style={{ fontSize: "var(--font-xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)" }}>
                  {formatPercentage(ct1Average)}
                </div>
                <div style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)", marginTop: "var(--space-1)" }}>
                  Early milestone performance
                </div>
              </div>
            </div>

            {/* Previous Semester Continuity Section (for Semester 2+) */}
            {currentSemester > 1 && (
              <div
                style={{
                  padding: "var(--space-4)",
                  backgroundColor: "var(--vcis-surface-soft)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-md)",
                }}
              >
                <div style={{ fontSize: "var(--font-xs)", fontWeight: "var(--font-weight-semibold)", color: "var(--vcis-accent)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "var(--space-3)" }}>
                  Historical Continuity (Semester {currentSemester - 1})
                </div>
                <div className="vcis-grid vcis-grid-2">
                  <div>
                    <span style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>Previous Semester Score: </span>
                    <strong style={{ fontSize: "var(--font-md)", color: "var(--vcis-text)" }}>
                      {formatPercentage(previousSemesterScore)}
                    </strong>
                  </div>
                  <div>
                    <span style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>Previous Semester Attendance: </span>
                    <strong style={{ fontSize: "var(--font-md)", color: "var(--vcis-text)" }}>
                      {formatPercentage(previousSemesterAttendance)}
                    </strong>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AcademicOverview;
