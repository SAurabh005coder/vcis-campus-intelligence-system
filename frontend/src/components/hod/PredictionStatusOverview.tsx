import React from "react";
import type { InterventionResponse } from "../../api/interventionApi";
import type { AcademicStatus } from "../../api/predictionApi";

interface PredictionStatusOverviewProps {
  interventions: InterventionResponse[];
  sessionEvaluations: Map<number, { score: number; status: AcademicStatus }>;
}

export const PredictionStatusOverview: React.FC<PredictionStatusOverviewProps> = ({
  interventions,
  sessionEvaluations,
}) => {
  // Count trigger academic status from existing persistent interventions
  const intervNormal = interventions.filter(
    (i) => i.trigger_academic_status === "NORMAL"
  ).length;
  const intervMonitor = interventions.filter(
    (i) => i.trigger_academic_status === "MONITOR"
  ).length;
  const intervIntervention = interventions.filter(
    (i) => i.trigger_academic_status === "INTERVENTION"
  ).length;

  // Count session evaluations run on-demand
  let sessionNormal = 0;
  let sessionMonitor = 0;
  let sessionIntervention = 0;

  sessionEvaluations.forEach((evalData) => {
    if (evalData.status === "NORMAL") sessionNormal++;
    else if (evalData.status === "MONITOR") sessionMonitor++;
    else if (evalData.status === "INTERVENTION") sessionIntervention++;
  });

  // Calculate cumulative observed distribution
  const totalNormal = intervNormal + sessionNormal;
  const totalMonitor = intervMonitor + sessionMonitor;
  const totalIntervention = intervIntervention + sessionIntervention;
  const totalObserved = totalNormal + totalMonitor + totalIntervention;

  const normalPct = totalObserved > 0 ? (totalNormal / totalObserved) * 100 : 0;
  const monitorPct = totalObserved > 0 ? (totalMonitor / totalObserved) * 100 : 0;
  const interventionPct = totalObserved > 0 ? (totalIntervention / totalObserved) * 100 : 0;

  return (
    <div className="vcis-card">
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Academic Status & Prediction Oversight</h3>
          <p className="vcis-card-subtitle">
            Observed student academic status from intervention records and on-demand evaluations
          </p>
        </div>
        <span className="vcis-badge vcis-badge-neutral">
          Decision Support
        </span>
      </div>

      <div className="vcis-card-body">
        {/* CSS-Only Visual Distribution Bar */}
        {totalObserved > 0 && (
          <div style={{ marginBottom: "var(--space-4)" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: "var(--vcis-font-size-xs)",
                color: "var(--vcis-text-muted)",
              }}
            >
              <span>Status Distribution ({totalObserved} observed)</span>
              <span>
                {normalPct.toFixed(0)}% Normal • {monitorPct.toFixed(0)}% Monitor • {interventionPct.toFixed(0)}% Intervention
              </span>
            </div>
            <div className="vcis-distribution-bar">
              <div
                className="vcis-distribution-segment vcis-distribution-segment-normal"
                style={{ width: `${normalPct}%` }}
                title={`Normal: ${totalNormal}`}
              />
              <div
                className="vcis-distribution-segment vcis-distribution-segment-monitor"
                style={{ width: `${monitorPct}%` }}
                title={`Monitor: ${totalMonitor}`}
              />
              <div
                className="vcis-distribution-segment vcis-distribution-segment-intervention"
                style={{ width: `${interventionPct}%` }}
                title={`Intervention: ${totalIntervention}`}
              />
            </div>
          </div>
        )}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "var(--space-3)",
            marginBottom: "var(--space-4)",
          }}
        >
          {/* NORMAL status */}
          <div
            style={{
              backgroundColor: "rgba(16, 185, 129, 0.06)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--vcis-status-normal-border)",
              borderLeft: "4px solid var(--vcis-success)",
              padding: "var(--space-3)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "var(--vcis-font-size-sm)", fontWeight: "var(--vcis-font-weight-bold)", color: "var(--vcis-status-normal-text)" }}>
                NORMAL
              </span>
              <span className="vcis-status vcis-status-normal">
                Good Standing
              </span>
            </div>
            <div style={{ marginTop: "var(--space-2)", fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-secondary)" }}>
              <div>Intervention Triggers: <strong>{intervNormal}</strong></div>
              <div>On-Demand Reviewed: <strong>{sessionNormal}</strong></div>
            </div>
          </div>

          {/* MONITOR status */}
          <div
            style={{
              backgroundColor: "rgba(245, 158, 11, 0.06)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--vcis-status-monitor-border)",
              borderLeft: "4px solid var(--vcis-warning)",
              padding: "var(--space-3)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "var(--vcis-font-size-sm)", fontWeight: "var(--vcis-font-weight-bold)", color: "var(--vcis-status-monitor-text)" }}>
                MONITOR
              </span>
              <span className="vcis-status vcis-status-monitor">
                Advisory Watch
              </span>
            </div>
            <div style={{ marginTop: "var(--space-2)", fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-secondary)" }}>
              <div>Intervention Triggers: <strong>{intervMonitor}</strong></div>
              <div>On-Demand Reviewed: <strong>{sessionMonitor}</strong></div>
            </div>
          </div>

          {/* INTERVENTION status */}
          <div
            style={{
              backgroundColor: "rgba(239, 68, 68, 0.06)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--vcis-status-intervention-border)",
              borderLeft: "4px solid var(--vcis-danger)",
              padding: "var(--space-3)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "var(--vcis-font-size-sm)", fontWeight: "var(--vcis-font-weight-bold)", color: "var(--vcis-status-intervention-text)" }}>
                INTERVENTION
              </span>
              <span className="vcis-status vcis-status-intervention">
                Remedial Action
              </span>
            </div>
            <div style={{ marginTop: "var(--space-2)", fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-secondary)" }}>
              <div>Intervention Triggers: <strong>{intervIntervention}</strong></div>
              <div>On-Demand Reviewed: <strong>{sessionIntervention}</strong></div>
            </div>
          </div>
        </div>

        <div
          style={{
            fontSize: "var(--vcis-font-size-xs)",
            color: "var(--vcis-text-muted)",
            backgroundColor: "var(--vcis-surface-soft)",
            padding: "var(--space-2) var(--space-3)",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--vcis-border)",
            lineHeight: 1.5,
          }}
        >
          ℹ️ Academic statuses and predicted scores are evaluated authoritatively by the backend ML service on-demand per student. In accordance with performance design guidelines, batch inference across the entire roster is not executed on page load.
        </div>
      </div>
    </div>
  );
};
