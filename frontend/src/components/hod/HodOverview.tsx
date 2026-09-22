import React from "react";
import type { HodProfile } from "../../api/hodApi";

interface HodOverviewProps {
  hod: HodProfile | null;
  departmentName: string;
  departmentCode?: string;
  totalStudentsCount: number;
  totalInterventionsCount: number;
}

export const HodOverview: React.FC<HodOverviewProps> = ({
  hod,
  departmentName,
  departmentCode,
  totalStudentsCount,
  totalInterventionsCount,
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
          <h1 className="vcis-welcome-title">
            {hod?.name || "Head of Department"}
          </h1>
          <p className="vcis-welcome-subtitle">
            {hod?.designation || "Department Academic Head"} • {hod?.email}
            {departmentName ? ` • Department of ${departmentName}` : ""}
          </p>
        </div>

        <div className="vcis-meta-pill-group">
          {/* Department Scope Pill */}
          <div className="vcis-meta-pill">
            <span className="vcis-meta-label">Oversight Scope:</span>
            <span className="vcis-meta-value" style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}>
              {departmentName}
              {departmentCode && (
                <span
                  style={{
                    backgroundColor: "rgba(59, 130, 246, 0.15)",
                    color: "var(--vcis-accent)",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "var(--radius-sm)",
                    fontSize: "0.75rem",
                    fontWeight: "var(--vcis-font-weight-semibold)",
                  }}
                >
                  {departmentCode}
                </span>
              )}
            </span>
          </div>

          {/* Enrolled Students Count */}
          <div className="vcis-meta-pill">
            <span className="vcis-meta-label">Roster:</span>
            <span className="vcis-meta-value" style={{ color: "var(--vcis-accent)" }}>
              {totalStudentsCount} Students
            </span>
          </div>

          {/* Department Interventions Count */}
          <div className="vcis-meta-pill">
            <span className="vcis-meta-label">Interventions:</span>
            <span className="vcis-meta-value" style={{ color: "#a855f7" }}>
              {totalInterventionsCount} Active
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
