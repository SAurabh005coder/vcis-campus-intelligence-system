import React, { useState } from "react";
import type { InterventionResponse } from "../../api/interventionApi";
import type {
  InterventionStatus,
  UpdateInterventionRequest,
} from "../../api/facultyApi";
import type { StudentProfile } from "../../api/studentApi";

interface InterventionTableProps {
  interventions: InterventionResponse[];
  myInterventions?: InterventionResponse[];
  isLoading: boolean;
  onUpdateIntervention: (
    id: number,
    payload: UpdateInterventionRequest
  ) => Promise<void>;
  studentName?: string;
  currentFacultyId: number | null;
  students?: StudentProfile[];
}

export const InterventionTable: React.FC<InterventionTableProps> = ({
  interventions,
  myInterventions = [],
  isLoading,
  onUpdateIntervention,
  studentName,
  currentFacultyId,
  students = [],
}) => {
  const [viewMode, setViewMode] = useState<"student" | "my_assigned">("student");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [newStatus, setNewStatus] = useState<InterventionStatus>("assigned");
  const [newActionPlan, setNewActionPlan] = useState("");
  const [newFollowUpDate, setNewFollowUpDate] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  // Determine active dataset based on viewMode
  const activeList = viewMode === "student" ? interventions : myInterventions;

  const formatType = (type: string) => {
    switch (type.toLowerCase()) {
      case "extra_class":
        return "Extra / Remedial Class";
      case "additional_assignment":
        return "Additional Assignment";
      case "counselling":
        return "Academic Counselling";
      case "monitoring":
        return "Performance Monitoring";
      default:
        return type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "assigned":
        return <span className="vcis-status vcis-status-neutral">Assigned</span>;
      case "in_progress":
        return <span className="vcis-status vcis-status-monitor">In Progress</span>;
      case "completed":
        return <span className="vcis-status vcis-status-normal">Completed</span>;
      case "dismissed":
      case "cancelled":
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

  const getStudentLabel = (studentId: number) => {
    const s = students.find((st) => st.id === studentId);
    if (s) {
      return `${s.name} (${s.roll_number})`;
    }
    return `Student #${studentId}`;
  };

  const startEdit = (item: InterventionResponse) => {
    setEditingId(item.id);
    setNewStatus(item.status as InterventionStatus);
    setNewActionPlan(item.action_plan || "");
    setNewFollowUpDate(item.follow_up_date || "");
    setUpdateError(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setUpdateError(null);
  };

  const handleSave = async (id: number) => {
    setIsSaving(true);
    setUpdateError(null);
    try {
      await onUpdateIntervention(id, {
        status: newStatus,
        action_plan: newActionPlan.trim() || null,
        follow_up_date: newFollowUpDate || null,
      });
      setEditingId(null);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setUpdateError(err.message);
      } else {
        setUpdateError("Failed to update intervention workflow.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="vcis-card">
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Academic Interventions</h3>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>
            Review, track, and update remedial actions and guidance workflows
          </p>
        </div>

        {/* View Mode Toggle */}
        <div className="vcis-tab-list" role="tablist" style={{ margin: 0 }}>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "student"}
            onClick={() => setViewMode("student")}
            className={`vcis-tab-btn ${viewMode === "student" ? "is-active" : ""}`}
            style={{ padding: "0.3rem 0.75rem", fontSize: "var(--font-xs)" }}
          >
            {studentName ? `${studentName.split(" ")[0]}'s Interventions` : "Selected Student"} ({interventions.length})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "my_assigned"}
            onClick={() => setViewMode("my_assigned")}
            className={`vcis-tab-btn ${viewMode === "my_assigned" ? "is-active" : ""}`}
            style={{ padding: "0.3rem 0.75rem", fontSize: "var(--font-xs)" }}
          >
            My Assigned ({myInterventions.length})
          </button>
        </div>
      </div>

      <div className="vcis-card-body">
        {updateError && (
          <div className="vcis-error" style={{ marginBottom: "var(--space-4)" }} role="alert">
            {updateError}
          </div>
        )}

        {isLoading ? (
          <div className="vcis-loading" style={{ padding: "var(--space-6) 0" }}>
            <div className="vcis-spinner" aria-hidden="true" />
            <span style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)" }}>
              Loading academic interventions...
            </span>
          </div>
        ) : activeList.length === 0 ? (
          <div className="vcis-empty">
            {viewMode === "student"
              ? "No interventions are currently recorded for this student."
              : "No interventions are currently assigned under your faculty profile."}
          </div>
        ) : (
          <div className="vcis-table-wrapper" style={{ maxHeight: "380px", overflowY: "auto" }}>
            <table className="vcis-table">
              <thead>
                <tr>
                  {viewMode === "my_assigned" && (
                    <th className="vcis-table-header">Student</th>
                  )}
                  <th className="vcis-table-header">Strategy / Type</th>
                  <th className="vcis-table-header">Trigger Context</th>
                  <th className="vcis-table-header" style={{ textAlign: "center" }}>Status</th>
                  <th className="vcis-table-header">Action Plan</th>
                  <th className="vcis-table-header">Review Date</th>
                  <th className="vcis-table-header" style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {activeList.map((item) => {
                  const isEditing = editingId === item.id;
                  const canEdit =
                    currentFacultyId !== null && item.faculty_id === currentFacultyId;

                  return (
                    <tr key={item.id} className="vcis-table-row">
                      {viewMode === "my_assigned" && (
                        <td className="vcis-table-cell" style={{ fontWeight: "var(--font-weight-semibold)" }}>
                          {getStudentLabel(item.student_id)}
                        </td>
                      )}
                      <td className="vcis-table-cell">
                        <div style={{ fontWeight: "var(--font-weight-semibold)", color: "var(--vcis-text)" }}>
                          {formatType(item.intervention_type)}
                        </div>
                        <div style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)" }}>
                          Sem {item.semester} • #{item.id}
                        </div>
                      </td>

                      <td className="vcis-table-cell" style={{ fontSize: "var(--font-xs)" }}>
                        {item.trigger_academic_status ? (
                          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
                            <span
                              className={`vcis-status ${
                                item.trigger_academic_status === "INTERVENTION"
                                  ? "vcis-status-danger"
                                  : item.trigger_academic_status === "MONITOR"
                                  ? "vcis-status-warning"
                                  : "vcis-status-neutral"
                              }`}
                              style={{ fontSize: "0.68rem" }}
                            >
                              {item.trigger_academic_status}
                            </span>
                            {item.trigger_predicted_score !== null && (
                              <span style={{ color: "var(--vcis-text-secondary)" }}>
                                ({item.trigger_predicted_score.toFixed(1)}%)
                              </span>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: "var(--vcis-text-muted)" }}>Manual Entry</span>
                        )}
                      </td>

                      <td className="vcis-table-cell" style={{ textAlign: "center" }}>
                        {isEditing ? (
                          <select
                            value={newStatus}
                            onChange={(e) => setNewStatus(e.target.value as InterventionStatus)}
                            className="vcis-select"
                            style={{ padding: "0.2rem 0.5rem", fontSize: "var(--font-xs)" }}
                            disabled={isSaving}
                          >
                            <option value="assigned">Assigned</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                            <option value="dismissed">Dismissed</option>
                          </select>
                        ) : (
                          getStatusBadge(item.status)
                        )}
                      </td>

                      <td className="vcis-table-cell" style={{ maxWidth: "240px", fontSize: "var(--font-xs)" }}>
                        {isEditing ? (
                          <textarea
                            value={newActionPlan}
                            onChange={(e) => setNewActionPlan(e.target.value)}
                            rows={2}
                            className="vcis-input"
                            style={{ width: "100%", fontSize: "var(--font-xs)", resize: "vertical" }}
                            disabled={isSaving}
                          />
                        ) : (
                          <div>
                            <div style={{ color: "var(--vcis-text)", lineHeight: 1.4 }}>
                              {item.action_plan}
                            </div>
                            {item.description && (
                              <div style={{ color: "var(--vcis-text-muted)", marginTop: "0.2rem" }}>
                                {item.description}
                              </div>
                            )}
                          </div>
                        )}
                      </td>

                      <td className="vcis-table-cell" style={{ fontSize: "var(--font-xs)", whiteSpace: "nowrap" }}>
                        {isEditing ? (
                          <input
                            type="date"
                            value={newFollowUpDate}
                            onChange={(e) => setNewFollowUpDate(e.target.value)}
                            className="vcis-input"
                            style={{ fontSize: "var(--font-xs)", padding: "0.2rem 0.4rem" }}
                            disabled={isSaving}
                          />
                        ) : (
                          <div>
                            <div>{formatDate(item.follow_up_date)}</div>
                            <div style={{ fontSize: "0.68rem", color: "var(--vcis-text-muted)" }}>
                              Assigned: {formatDate(item.created_at)}
                            </div>
                          </div>
                        )}
                      </td>

                      <td className="vcis-table-cell" style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                        {isEditing ? (
                          <div style={{ display: "flex", justifyContent: "flex-end", gap: "var(--space-1)" }}>
                            <button
                              type="button"
                              onClick={() => handleSave(item.id)}
                              disabled={isSaving}
                              className="vcis-button vcis-button-primary vcis-button-sm"
                              style={{ padding: "0.2rem 0.5rem", fontSize: "var(--font-xs)" }}
                            >
                              {isSaving ? "Saving..." : "Save"}
                            </button>
                            <button
                              type="button"
                              onClick={cancelEdit}
                              disabled={isSaving}
                              className="vcis-button vcis-button-secondary vcis-button-sm"
                              style={{ padding: "0.2rem 0.5rem", fontSize: "var(--font-xs)" }}
                            >
                              Cancel
                            </button>
                          </div>
                        ) : canEdit ? (
                          <button
                            type="button"
                            onClick={() => startEdit(item)}
                            className="vcis-button vcis-button-secondary vcis-button-sm"
                            style={{ padding: "0.2rem 0.5rem", fontSize: "var(--font-xs)" }}
                          >
                            Update
                          </button>
                        ) : (
                          <span style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)" }}>
                            Read-Only
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default InterventionTable;
