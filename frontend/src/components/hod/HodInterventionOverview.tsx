import React from "react";
import type { InterventionResponse } from "../../api/interventionApi";

interface HodInterventionOverviewProps {
  interventions: InterventionResponse[];
}

export const HodInterventionOverview: React.FC<HodInterventionOverviewProps> = ({
  interventions,
}) => {
  // Compute lifecycle status counts from actual records
  const assignedCount = interventions.filter(
    (i) => i.status.toLowerCase() === "assigned"
  ).length;
  const inProgressCount = interventions.filter(
    (i) => i.status.toLowerCase() === "in_progress"
  ).length;
  const completedCount = interventions.filter(
    (i) => i.status.toLowerCase() === "completed"
  ).length;
  const dismissedCount = interventions.filter(
    (i) =>
      i.status.toLowerCase() === "dismissed" ||
      i.status.toLowerCase() === "cancelled"
  ).length;

  // Compute intervention type counts
  const extraClassCount = interventions.filter(
    (i) => i.intervention_type.toLowerCase() === "extra_class"
  ).length;
  const assignmentCount = interventions.filter(
    (i) => i.intervention_type.toLowerCase() === "additional_assignment"
  ).length;
  const counsellingCount = interventions.filter(
    (i) => i.intervention_type.toLowerCase() === "counselling"
  ).length;
  const monitoringCount = interventions.filter(
    (i) => i.intervention_type.toLowerCase() === "monitoring"
  ).length;

  return (
    <div className="vcis-card">
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Intervention Oversight & Progress</h3>
          <p className="vcis-card-subtitle">
            Lifecycle monitoring and strategy breakdown across departmental interventions
          </p>
        </div>
        <span className="vcis-badge vcis-badge-neutral">
          {interventions.length} Total
        </span>
      </div>

      <div className="vcis-card-body">
        {/* Lifecycle Status Metrics */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
            gap: "var(--space-3)",
            marginBottom: "var(--space-4)",
          }}
        >
          {/* Total Interventions */}
          <div
            style={{
              backgroundColor: "var(--vcis-surface-soft)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--vcis-border)",
              padding: "var(--space-3)",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)", marginBottom: "var(--space-1)" }}>
              Total Actions
            </div>
            <div style={{ fontSize: "var(--vcis-font-size-xl)", fontWeight: "var(--vcis-font-weight-bold)", color: "var(--vcis-accent)" }}>
              {interventions.length}
            </div>
          </div>

          {/* Assigned */}
          <div
            style={{
              backgroundColor: "rgba(59, 130, 246, 0.08)",
              borderRadius: "var(--radius-md)",
              border: "1px solid rgba(59, 130, 246, 0.2)",
              padding: "var(--space-3)",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-accent)", marginBottom: "var(--space-1)" }}>
              Assigned
            </div>
            <div style={{ fontSize: "var(--vcis-font-size-xl)", fontWeight: "var(--vcis-font-weight-bold)", color: "var(--vcis-accent)" }}>
              {assignedCount}
            </div>
          </div>

          {/* In Progress */}
          <div
            style={{
              backgroundColor: "rgba(245, 158, 11, 0.08)",
              borderRadius: "var(--radius-md)",
              border: "1px solid rgba(245, 158, 11, 0.2)",
              padding: "var(--space-3)",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-warning)", marginBottom: "var(--space-1)" }}>
              In Progress
            </div>
            <div style={{ fontSize: "var(--vcis-font-size-xl)", fontWeight: "var(--vcis-font-weight-bold)", color: "var(--vcis-warning)" }}>
              {inProgressCount}
            </div>
          </div>

          {/* Completed */}
          <div
            style={{
              backgroundColor: "rgba(16, 185, 129, 0.08)",
              borderRadius: "var(--radius-md)",
              border: "1px solid rgba(16, 185, 129, 0.2)",
              padding: "var(--space-3)",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-success)", marginBottom: "var(--space-1)" }}>
              Completed
            </div>
            <div style={{ fontSize: "var(--vcis-font-size-xl)", fontWeight: "var(--vcis-font-weight-bold)", color: "var(--vcis-success)" }}>
              {completedCount}
            </div>
          </div>

          {/* Dismissed */}
          <div
            style={{
              backgroundColor: "var(--vcis-surface-muted)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--vcis-border)",
              padding: "var(--space-3)",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)", marginBottom: "var(--space-1)" }}>
              Dismissed
            </div>
            <div style={{ fontSize: "var(--vcis-font-size-xl)", fontWeight: "var(--vcis-font-weight-bold)", color: "var(--vcis-text-secondary)" }}>
              {dismissedCount}
            </div>
          </div>
        </div>

        {/* Intervention Strategy Types Breakdown */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "var(--space-4)",
            fontSize: "var(--vcis-font-size-xs)",
            backgroundColor: "var(--vcis-surface-soft)",
            padding: "var(--space-3) var(--space-4)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--vcis-border)",
            color: "var(--vcis-text-secondary)",
          }}
        >
          <div>
            <span>Remedial Classes: </span>
            <strong style={{ color: "var(--vcis-text)" }}>{extraClassCount}</strong>
          </div>
          <div>
            <span>Additional Assignments: </span>
            <strong style={{ color: "var(--vcis-text)" }}>{assignmentCount}</strong>
          </div>
          <div>
            <span>Academic Counselling: </span>
            <strong style={{ color: "var(--vcis-text)" }}>{counsellingCount}</strong>
          </div>
          <div>
            <span>Monitoring: </span>
            <strong style={{ color: "var(--vcis-text)" }}>{monitoringCount}</strong>
          </div>
        </div>
      </div>
    </div>
  );
};
