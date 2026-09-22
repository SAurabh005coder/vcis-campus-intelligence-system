import React from "react";
import type { FacultyProfile } from "../../api/facultyApi";
import type { DepartmentInfo } from "../../api/studentApi";

interface FacultyOverviewProps {
  faculty: FacultyProfile | null;
  department: DepartmentInfo | null;
  email?: string;
  totalStudents: number;
}

export const FacultyOverview: React.FC<FacultyOverviewProps> = ({
  faculty,
  department,
  email,
  totalStudents,
}) => {
  return (
    <div className="vcis-welcome-card" style={{ marginBottom: "var(--space-6)" }}>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "var(--space-4)",
        }}
      >
        <div>
          <h2
            style={{
              margin: 0,
              fontSize: "var(--vcis-text-2xl)",
              fontWeight: "var(--vcis-font-bold)",
              color: "var(--vcis-text-primary)",
              letterSpacing: "-0.02em",
            }}
          >
            {faculty
              ? `${faculty.first_name} ${faculty.last_name}`
              : "Faculty Member"}
          </h2>
          <p
            style={{
              margin: "var(--vcis-space-1) 0 0 0",
              fontSize: "var(--vcis-text-sm)",
              color: "var(--vcis-text-muted)",
            }}
          >
            {faculty?.designation || "Faculty Academic Advisor"}
            {department ? ` • Department of ${department.name}` : ""}
            {email ? ` • ${email}` : ""}
          </p>
        </div>

        <div className="vcis-meta-pill-group">
          <div className="vcis-meta-pill">
            <span>Employee Code:</span>
            <strong>{faculty?.employee_code || "N/A"}</strong>
          </div>
          <div className="vcis-meta-pill">
            <span>Faculty ID:</span>
            <strong>{faculty ? `#${faculty.id}` : "N/A"}</strong>
          </div>
          <div className="vcis-meta-pill" style={{ borderColor: "var(--vcis-primary-border)" }}>
            <span>Students Accessible:</span>
            <strong style={{ color: "var(--vcis-primary-text)" }}>{totalStudents}</strong>
          </div>
        </div>
      </div>

      {!faculty && (
        <div
          className="vcis-alert vcis-alert-warning"
          style={{
            marginTop: "var(--space-4)",
            padding: "var(--space-3) var(--space-4)",
            borderRadius: "var(--radius-md)",
            fontSize: "var(--font-xs)",
          }}
        >
          <strong>Faculty Profile Notice:</strong> Your account is not currently linked to an active faculty record in the institution registry. You can browse student records, but assigning academic interventions requires a linked faculty profile.
        </div>
      )}
    </div>
  );
};

export default FacultyOverview;
