import React from "react";
import type { EnrollmentPerformanceProfileResponse } from "../../api/studentApi";

interface AttendanceOverviewProps {
  performanceProfiles: EnrollmentPerformanceProfileResponse[];
  overallAttendance?: number | null;
  isLoading: boolean;
}

export const AttendanceOverview: React.FC<AttendanceOverviewProps> = ({
  performanceProfiles,
  overallAttendance,
  isLoading,
}) => {
  const formatPercentage = (val?: number | null) => {
    if (val === undefined || val === null || isNaN(val)) {
      return "N/A";
    }
    return `${val.toFixed(1)}%`;
  };

  // Calculate overall metrics from backend profiles if available
  const totalClasses = performanceProfiles.reduce((acc, p) => acc + p.total_classes, 0);
  const totalPresent = performanceProfiles.reduce((acc, p) => acc + p.present_classes, 0);
  const totalAbsent = performanceProfiles.reduce((acc, p) => acc + p.absent_classes, 0);

  const calculatedOverall =
    totalClasses > 0 ? (totalPresent / totalClasses) * 100 : overallAttendance ?? 0;

  return (
    <div className="vcis-card">
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Attendance Records</h3>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>
            Session-level attendance logging and course-wise breakdown
          </p>
        </div>
      </div>

      <div className="vcis-card-body">
        {isLoading ? (
          <div className="vcis-loading" style={{ padding: "var(--space-6) 0" }}>
            <div className="vcis-spinner" aria-hidden="true" />
            <span style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)" }}>
              Loading attendance records...
            </span>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
            {/* Progress Bar Container */}
            <div
              style={{
                backgroundColor: "var(--vcis-surface-raised)",
                border: "1px solid var(--vcis-border)",
                borderRadius: "var(--radius-lg)",
                padding: "var(--space-5)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <div>
                  <span className="vcis-kpi-label">Cumulative Attendance</span>
                  <div style={{ fontSize: "var(--font-2xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)" }}>
                    {formatPercentage(calculatedOverall)}
                  </div>
                </div>
                <div style={{ textAlign: "right", fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)" }}>
                  <div>{totalPresent} Present • {totalAbsent} Absent</div>
                  <div>{totalClasses} Recorded Sessions</div>
                </div>
              </div>

              {/* Visual Progress Bar */}
              <div className="vcis-progress-container" title={`Cumulative attendance: ${calculatedOverall.toFixed(1)}%`}>
                <div
                  className="vcis-progress-bar"
                  style={{
                    width: `${Math.min(100, Math.max(0, calculatedOverall))}%`,
                    backgroundColor: "var(--vcis-primary)",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)" }}>
                <span>0%</span>
                <span>100%</span>
              </div>
            </div>

            {/* Subject-Level Attendance Breakdown */}
            {performanceProfiles.length > 0 ? (
              <div>
                <h4
                  style={{
                    fontSize: "var(--font-sm)",
                    fontWeight: "var(--font-weight-semibold)",
                    color: "var(--vcis-text)",
                    marginBottom: "var(--space-3)",
                  }}
                >
                  Course-Wise Attendance Records
                </h4>
                <div className="vcis-table-wrapper">
                  <table className="vcis-table">
                    <thead>
                      <tr>
                        <th className="vcis-table-header">Subject Code</th>
                        <th className="vcis-table-header">Subject Name</th>
                        <th className="vcis-table-header" style={{ textAlign: "center" }}>Present</th>
                        <th className="vcis-table-header" style={{ textAlign: "center" }}>Absent</th>
                        <th className="vcis-table-header" style={{ textAlign: "center" }}>Total Classes</th>
                        <th className="vcis-table-header" style={{ textAlign: "right" }}>Percentage</th>
                      </tr>
                    </thead>
                    <tbody>
                      {performanceProfiles.map((p) => {
                        const subPercent =
                          p.total_classes > 0 ? (p.present_classes / p.total_classes) * 100 : 0;
                        return (
                          <tr key={p.enrollment_id} className="vcis-table-row">
                            <td className="vcis-table-cell" style={{ fontWeight: "var(--font-weight-semibold)" }}>
                              {p.subject_code}
                            </td>
                            <td className="vcis-table-cell">{p.subject_name}</td>
                            <td className="vcis-table-cell" style={{ textAlign: "center", color: "var(--vcis-success)" }}>
                              {p.present_classes}
                            </td>
                            <td className="vcis-table-cell" style={{ textAlign: "center", color: p.absent_classes > 0 ? "var(--vcis-danger)" : "var(--vcis-text-muted)" }}>
                              {p.absent_classes}
                            </td>
                            <td className="vcis-table-cell" style={{ textAlign: "center" }}>
                              {p.total_classes}
                            </td>
                            <td className="vcis-table-cell" style={{ textAlign: "right", fontWeight: "var(--font-weight-bold)" }}>
                              {formatPercentage(subPercent)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="vcis-empty">
                No subject-level attendance records found for the current term.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AttendanceOverview;
