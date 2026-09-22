import React from "react";

interface AcademicKpiGridProps {
  currentSemester: number;
  currentAttendance?: number | null;
  currentCt1Average?: number | null;
  currentAssignmentAverage?: number | null;
  isLoading?: boolean;
}

export const AcademicKpiGrid: React.FC<AcademicKpiGridProps> = ({
  currentSemester,
  currentAttendance,
  currentCt1Average,
  currentAssignmentAverage,
  isLoading,
}) => {
  const formatValue = (val?: number | null) => {
    if (val === undefined || val === null || isNaN(val)) {
      return "Not recorded";
    }
    return `${val.toFixed(1)}%`;
  };

  return (
    <div className="vcis-kpi-grid" role="region" aria-label="Academic Key Performance Indicators">
      {/* KPI 1: Cumulative Attendance */}
      <div className="vcis-kpi-card">
        <div>
          <div className="vcis-kpi-value">
            {isLoading ? "—" : formatValue(currentAttendance)}
          </div>
          <div className="vcis-kpi-label">Current Attendance</div>
        </div>
        <div className="vcis-kpi-context">
          Recorded term attendance
        </div>
      </div>

      {/* KPI 2: Cycle Test 1 Average */}
      <div className="vcis-kpi-card">
        <div>
          <div className="vcis-kpi-value">
            {isLoading ? "—" : formatValue(currentCt1Average)}
          </div>
          <div className="vcis-kpi-label">CT1 Average</div>
        </div>
        <div className="vcis-kpi-context">
          Early milestone evaluation
        </div>
      </div>

      {/* KPI 3: Continuous Assignment Average */}
      <div className="vcis-kpi-card">
        <div>
          <div className="vcis-kpi-value">
            {isLoading ? "—" : formatValue(currentAssignmentAverage)}
          </div>
          <div className="vcis-kpi-label">Assignment Average</div>
        </div>
        <div className="vcis-kpi-context">
          Continuous internal assessments
        </div>
      </div>

      {/* KPI 4: Current Academic Term */}
      <div className="vcis-kpi-card">
        <div>
          <div className="vcis-kpi-value">
            Sem {currentSemester}
          </div>
          <div className="vcis-kpi-label">Current Semester</div>
        </div>
        <div className="vcis-kpi-context">
          Active progression stage
        </div>
      </div>
    </div>
  );
};

export default AcademicKpiGrid;
