import React, { useEffect, useState } from "react";
import {
  type StudentSemesterResultResponse,
  getStudentSemesterResult,
} from "../../api/studentApi";

interface SemesterHistoryProps {
  studentId: number;
  currentSemester: number;
  totalSemesters?: number;
}

export const SemesterHistory: React.FC<SemesterHistoryProps> = ({
  studentId,
  currentSemester,
  totalSemesters = 4,
}) => {
  const [selectedSemester, setSelectedSemester] = useState<number>(currentSemester);
  const [semesterData, setSemesterData] = useState<StudentSemesterResultResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    let isCancelled = false;
    setIsLoading(true);
    setSemesterData(null);

    getStudentSemesterResult(studentId, selectedSemester)
      .then((data) => {
        if (!isCancelled) {
          setSemesterData(data);
        }
      })
      .catch(() => {
        if (!isCancelled) {
          setSemesterData(null);
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [studentId, selectedSemester]);

  const formatPercentage = (val?: number | null) => {
    if (val === undefined || val === null || isNaN(val)) {
      return "N/A";
    }
    return `${val.toFixed(1)}%`;
  };

  const semestersList = Array.from({ length: totalSemesters }, (_, i) => i + 1);

  return (
    <div className="vcis-card">
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Academic Progression & History</h3>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>
            Verified multi-term academic trajectory and credit completion
          </p>
        </div>

        {/* Visual Trajectory Progression */}
        <div className="vcis-trajectory" aria-label="Semester progression trajectory">
          {semestersList.map((sem, idx) => {
            const isCurrent = sem === currentSemester;
            const isPast = sem < currentSemester;
            return (
              <React.Fragment key={sem}>
                <div
                  className="vcis-trajectory-node"
                  style={{
                    backgroundColor: isCurrent
                      ? "var(--vcis-primary-soft)"
                      : isPast
                      ? "var(--vcis-surface-raised)"
                      : "transparent",
                    borderColor: isCurrent
                      ? "var(--vcis-primary)"
                      : "var(--vcis-border)",
                    color: isCurrent
                      ? "var(--vcis-primary-hover)"
                      : isPast
                      ? "var(--vcis-text)"
                      : "var(--vcis-text-muted)",
                  }}
                >
                  Sem {sem} {isCurrent ? "(Current)" : ""}
                </div>
                {idx < semestersList.length - 1 && (
                  <span className="vcis-trajectory-arrow">→</span>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      <div className="vcis-card-body">
        {/* Semester Selection Tab Strip */}
        <div className="vcis-tab-list" role="tablist" aria-label="Select Semester">
          {semestersList.map((sem) => {
            const isSelected = sem === selectedSemester;
            const isCurrent = sem === currentSemester;
            return (
              <button
                key={sem}
                type="button"
                role="tab"
                aria-selected={isSelected}
                onClick={() => setSelectedSemester(sem)}
                className={`vcis-tab-btn ${isSelected ? "is-active" : ""}`}
              >
                Semester {sem} {isCurrent ? "★ Active" : ""}
              </button>
            );
          })}
        </div>

        {isLoading ? (
          <div className="vcis-loading" style={{ padding: "var(--space-6) 0" }}>
            <div className="vcis-spinner" aria-hidden="true" />
            <span style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)" }}>
              Loading Semester {selectedSemester} records...
            </span>
          </div>
        ) : !semesterData ? (
          <div className="vcis-empty">
            Historical data unavailable for Semester {selectedSemester}.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
            {/* Semester Metrics Summary */}
            <div className="vcis-grid vcis-grid-3">
              <div
                style={{
                  backgroundColor: "var(--vcis-surface-raised)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-4)",
                }}
              >
                <div className="vcis-kpi-label">Semester Result</div>
                <div style={{ fontSize: "var(--font-2xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)" }}>
                  {formatPercentage(semesterData.overall_percentage)}
                </div>
                <div className="vcis-kpi-context">Cumulative term average</div>
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
                <div style={{ fontSize: "var(--font-2xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-accent)" }}>
                  {semesterData.total_credits} Credits
                </div>
                <div className="vcis-kpi-context">{semesterData.total_subjects} Registered courses</div>
              </div>

              <div
                style={{
                  backgroundColor: "var(--vcis-surface-raised)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-4)",
                }}
              >
                <div className="vcis-kpi-label">Total Marks Obtained</div>
                <div style={{ fontSize: "var(--font-xl)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-success)" }}>
                  {semesterData.total_obtained_marks} / {semesterData.total_max_marks}
                </div>
                <div className="vcis-kpi-context">Aggregate term marks</div>
              </div>
            </div>

            {/* Courses / Subjects in Selected Semester */}
            {semesterData.subjects && semesterData.subjects.length > 0 ? (
              <div className="vcis-table-wrapper">
                <table className="vcis-table">
                  <thead>
                    <tr>
                      <th className="vcis-table-header">Course Code</th>
                      <th className="vcis-table-header">Subject Name</th>
                      <th className="vcis-table-header" style={{ textAlign: "center" }}>Credits</th>
                      <th className="vcis-table-header" style={{ textAlign: "right" }}>Marks Obtained</th>
                      <th className="vcis-table-header" style={{ textAlign: "center" }}>Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {semesterData.subjects.map((sub, idx) => (
                      <tr key={sub.subject_code || idx} className="vcis-table-row">
                        <td className="vcis-table-cell" style={{ fontWeight: "var(--font-weight-semibold)" }}>
                          {sub.subject_code}
                        </td>
                        <td className="vcis-table-cell">{sub.subject_name}</td>
                        <td className="vcis-table-cell" style={{ textAlign: "center", color: "var(--vcis-text-muted)" }}>
                          {sub.credits}
                        </td>
                        <td className="vcis-table-cell" style={{ textAlign: "right", color: "var(--vcis-text-muted)" }}>
                          {sub.total_obtained_marks} / {sub.total_max_marks}
                        </td>
                        <td className="vcis-table-cell" style={{ textAlign: "center", fontWeight: "var(--font-weight-semibold)", color: "var(--vcis-text)" }}>
                          {sub.overall_percentage.toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="vcis-empty">
                No subject records logged for Semester {selectedSemester}.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SemesterHistory;
