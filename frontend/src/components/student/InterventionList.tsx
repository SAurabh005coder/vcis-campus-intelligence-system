import React from "react";
import type { InterventionResponse } from "../../api/interventionApi";

interface InterventionListProps {
  interventions: InterventionResponse[];
  isLoading: boolean;
  errorMessage: string | null;
}

export const InterventionList: React.FC<InterventionListProps> = ({
  interventions,
  isLoading,
  errorMessage,
}) => {
  const formatType = (type: string) => {
    switch (type.toUpperCase()) {
      case "EXTRA_CLASS":
        return "Extra / Remedial Class";
      case "ADDITIONAL_ASSIGNMENT":
        return "Additional Assignment";
      case "COUNSELLING":
        return "Academic Counselling";
      case "MONITORING":
        return "Performance Monitoring";
      default:
        return type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case "ASSIGNED":
        return <span className="vcis-status vcis-status-info">Assigned</span>;
      case "IN_PROGRESS":
        return <span className="vcis-status vcis-status-warning">In Progress</span>;
      case "COMPLETED":
        return <span className="vcis-status vcis-status-success">Completed</span>;
      case "DISMISSED":
      case "CANCELLED":
        return <span className="vcis-status vcis-status-neutral">Dismissed</span>;
      default:
        return <span className="vcis-status vcis-status-neutral">{status}</span>;
    }
  };

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return "Not set";
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="vcis-card">
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Academic Interventions</h3>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>
            Faculty assigned academic guidance, remedial plans, and review schedules (Read-Only)
          </p>
        </div>

        <span
          className="vcis-status vcis-status-neutral"
          style={{ fontSize: "var(--font-xs)" }}
        >
          {interventions.length} {interventions.length === 1 ? "Record" : "Records"}
        </span>
      </div>

      <div className="vcis-card-body">
        {isLoading ? (
          <div className="vcis-loading" style={{ padding: "var(--space-6) 0" }}>
            <div className="vcis-spinner" aria-hidden="true" />
            <span style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)" }}>
              Loading intervention records...
            </span>
          </div>
        ) : errorMessage ? (
          <div className="vcis-error" role="alert">
            {errorMessage}
          </div>
        ) : interventions.length === 0 ? (
          <div className="vcis-empty">
            No academic interventions are currently assigned.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
            {interventions.map((item) => (
              <div
                key={item.id}
                style={{
                  backgroundColor: "var(--vcis-surface-raised)",
                  border: "1px solid var(--vcis-border)",
                  borderRadius: "var(--radius-lg)",
                  padding: "var(--space-4) var(--space-5)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--space-3)",
                }}
              >
                {/* Intervention Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "var(--space-2)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
                    <span style={{ fontSize: "var(--font-md)", fontWeight: "var(--font-weight-bold)", color: "var(--vcis-text)" }}>
                      {formatType(item.intervention_type)}
                    </span>
                    <span style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)" }}>
                      #{item.id}
                    </span>
                  </div>
                  {getStatusBadge(item.status)}
                </div>

                {/* Reason / Academic Trigger & Notes */}
                <div style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)", lineHeight: 1.5 }}>
                  {item.trigger_academic_status && (
                    <div style={{ marginBottom: "var(--space-1)" }}>
                      <strong style={{ color: "var(--vcis-text)" }}>Trigger Status: </strong>
                      <span className="vcis-status vcis-status-intervention" style={{ fontSize: "0.68rem" }}>
                        {item.trigger_academic_status}
                      </span>
                      {item.trigger_predicted_score !== null && (
                        <span style={{ marginLeft: "var(--space-2)", fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)" }}>
                          (Score Trigger: {item.trigger_predicted_score.toFixed(1)}%)
                        </span>
                      )}
                    </div>
                  )}
                  {item.description && (
                    <div>
                      <strong style={{ color: "var(--vcis-text)" }}>Details: </strong>
                      {item.description}
                    </div>
                  )}
                  {item.notes && (
                    <div style={{ marginTop: "var(--space-1)" }}>
                      <strong style={{ color: "var(--vcis-text)" }}>Faculty Notes: </strong>
                      {item.notes}
                    </div>
                  )}
                </div>

                {/* Action Plan if any */}
                {item.action_plan && (
                  <div
                    style={{
                      padding: "var(--space-3)",
                      backgroundColor: "var(--vcis-surface)",
                      borderRadius: "var(--radius-md)",
                      border: "1px solid var(--vcis-border)",
                      fontSize: "var(--font-xs)",
                      color: "var(--vcis-text-secondary)",
                    }}
                  >
                    <strong style={{ color: "var(--vcis-accent)" }}>Action Plan: </strong>
                    {item.action_plan}
                  </div>
                )}

                {/* Metadata details */}
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "var(--space-4)",
                    fontSize: "var(--font-xs)",
                    color: "var(--vcis-text-muted)",
                    borderTop: "1px solid var(--vcis-border)",
                    paddingTop: "var(--space-2)",
                  }}
                >
                  <div>Assigned: {formatDate(item.created_at)}</div>
                  {item.follow_up_date && (
                    <div>Scheduled Follow-up: <strong style={{ color: "var(--vcis-text)" }}>{formatDate(item.follow_up_date)}</strong></div>
                  )}
                  <div>Last Updated: {formatDate(item.updated_at)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default InterventionList;
