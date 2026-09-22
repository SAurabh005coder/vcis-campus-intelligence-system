import React, { useState, useMemo } from "react";
import type { InterventionResponse } from "../../api/interventionApi";
import type { StudentProfile } from "../../api/studentApi";
import type { FacultyProfile } from "../../api/facultyApi";
import type { UpdateInterventionRequest } from "../../api/adminApi";

interface AdminInterventionOverviewProps {
  interventions: InterventionResponse[];
  students?: StudentProfile[];
  faculty?: FacultyProfile[];
  onUpdateIntervention?: (id: number, payload: UpdateInterventionRequest) => Promise<void>;
  isLoading?: boolean;
}

export const AdminInterventionOverview: React.FC<AdminInterventionOverviewProps> = ({
  interventions,
  students = [],
  faculty = [],
  onUpdateIntervention,
  isLoading,
}) => {
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");

  // Editing state for Admin oversight updates
  const [editingId, setEditingId] = useState<number | null>(null);
  const [newStatus, setNewStatus] = useState<string>("assigned");
  const [newActionPlan, setNewActionPlan] = useState<string>("");
  const [newFollowUpDate, setNewFollowUpDate] = useState<string>("");
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  // Status counts
  const assignedCount = interventions.filter((i) => i.status.toLowerCase() === "assigned").length;
  const inProgressCount = interventions.filter((i) => i.status.toLowerCase() === "in_progress").length;
  const completedCount = interventions.filter((i) => i.status.toLowerCase() === "completed").length;
  const dismissedCount = interventions.filter(
    (i) => i.status.toLowerCase() === "dismissed" || i.status.toLowerCase() === "cancelled"
  ).length;

  const extraClassCount = interventions.filter((i) => i.intervention_type.toLowerCase() === "extra_class").length;
  const assignmentCount = interventions.filter((i) => i.intervention_type.toLowerCase() === "additional_assignment").length;
  const counsellingCount = interventions.filter((i) => i.intervention_type.toLowerCase() === "counselling").length;
  const monitoringCount = interventions.filter((i) => i.intervention_type.toLowerCase() === "monitoring").length;

  const studentMap = useMemo(() => {
    const map = new Map<number, string>();
    students.forEach((s) => map.set(s.id, `${s.name} (${s.roll_number})`));
    return map;
  }, [students]);

  const facultyMap = useMemo(() => {
    const map = new Map<number, string>();
    faculty.forEach((f) => map.set(f.id, `${f.first_name} ${f.last_name} (${f.employee_code})`));
    return map;
  }, [faculty]);

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

  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "assigned":
        return "vcis-badge-assigned";
      case "in_progress":
        return "vcis-badge-in-progress";
      case "completed":
        return "vcis-badge-completed";
      case "dismissed":
      case "cancelled":
        return "vcis-badge-dismissed";
      default:
        return "vcis-badge-neutral";
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

  const startEdit = (item: InterventionResponse) => {
    setEditingId(item.id);
    setNewStatus(item.status);
    setNewActionPlan(item.action_plan || "");
    setNewFollowUpDate(item.follow_up_date || "");
    setUpdateError(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setUpdateError(null);
  };

  const handleSave = async (id: number) => {
    if (!onUpdateIntervention) return;
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
        setUpdateError("Failed to update intervention workflow record.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  const filteredInterventions = useMemo(() => {
    return interventions.filter((item) => {
      const studentLabel = studentMap.get(item.student_id) || `Student #${item.student_id}`;
      const facultyLabel = facultyMap.get(item.faculty_id) || `Faculty #${item.faculty_id}`;
      const matchesSearch =
        studentLabel.toLowerCase().includes(searchTerm.toLowerCase()) ||
        facultyLabel.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.action_plan.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus =
        statusFilter === "all" || item.status.toLowerCase() === statusFilter.toLowerCase();
      const matchesType =
        typeFilter === "all" || item.intervention_type.toLowerCase() === typeFilter.toLowerCase();

      return matchesSearch && matchesStatus && matchesType;
    });
  }, [interventions, searchTerm, statusFilter, typeFilter, studentMap, facultyMap]);

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)" }}>
      {/* Header */}
      <div className="vcis-card-header">
        <div>
          <h3 style={{ margin: 0, fontSize: "var(--vcis-font-size-md)", fontWeight: "var(--vcis-font-weight-semibold)", color: "var(--vcis-text)" }}>
            Institutional Intervention Tracking & Oversight
          </h3>
          <p style={{ margin: "var(--space-1) 0 0 0", fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
            System-wide distribution of remedial academic interventions and lifecycle operations
          </p>
        </div>
        <span
          className="vcis-meta-pill"
        >
          <span className="vcis-meta-label">Scope:</span>
          <span className="vcis-meta-value">{interventions.length} Tracked</span>
        </span>
      </div>

      <div className="vcis-card-body">
        {/* System Lifecycle Metrics Distribution */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
            gap: "var(--space-3)",
            marginBottom: "var(--space-4)",
          }}
        >
          <div className="vcis-kpi-card" style={{ padding: "var(--space-3) var(--space-4)", minHeight: "auto" }}>
            <div>
              <div className="vcis-kpi-value" style={{ fontSize: "1.45rem", color: "var(--vcis-text)" }}>
                {interventions.length}
              </div>
              <div className="vcis-kpi-label">Total</div>
            </div>
            <div className="vcis-kpi-context">All lifecycles</div>
          </div>

          <div className="vcis-kpi-card" style={{ padding: "var(--space-3) var(--space-4)", minHeight: "auto", borderTop: "2px solid #3b82f6" }}>
            <div>
              <div className="vcis-kpi-value" style={{ fontSize: "1.45rem", color: "var(--vcis-primary)" }}>
                {assignedCount}
              </div>
              <div className="vcis-kpi-label">Assigned</div>
            </div>
            <div className="vcis-kpi-context">Pending start</div>
          </div>

          <div className="vcis-kpi-card" style={{ padding: "var(--space-3) var(--space-4)", minHeight: "auto", borderTop: "2px solid #f59e0b" }}>
            <div>
              <div className="vcis-kpi-value" style={{ fontSize: "1.45rem", color: "var(--vcis-warning)" }}>
                {inProgressCount}
              </div>
              <div className="vcis-kpi-label">In Progress</div>
            </div>
            <div className="vcis-kpi-context">Active sessions</div>
          </div>

          <div className="vcis-kpi-card" style={{ padding: "var(--space-3) var(--space-4)", minHeight: "auto", borderTop: "2px solid #10b981" }}>
            <div>
              <div className="vcis-kpi-value" style={{ fontSize: "1.45rem", color: "var(--vcis-success)" }}>
                {completedCount}
              </div>
              <div className="vcis-kpi-label">Completed</div>
            </div>
            <div className="vcis-kpi-context">Remediated</div>
          </div>

          <div className="vcis-kpi-card" style={{ padding: "var(--space-3) var(--space-4)", minHeight: "auto", borderTop: "2px solid #64748b" }}>
            <div>
              <div className="vcis-kpi-value" style={{ fontSize: "1.45rem", color: "var(--vcis-text-secondary)" }}>
                {dismissedCount}
              </div>
              <div className="vcis-kpi-label">Dismissed</div>
            </div>
            <div className="vcis-kpi-context">Cancelled</div>
          </div>
        </div>

        {/* Type Breakdown Bar */}
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
            marginBottom: "var(--space-4)",
          }}
        >
          <div>
            <span style={{ color: "var(--vcis-text-muted)" }}>Remedial Classes: </span>
            <strong style={{ color: "var(--vcis-text)" }}>{extraClassCount}</strong>
          </div>
          <div>
            <span style={{ color: "var(--vcis-text-muted)" }}>Additional Assignments: </span>
            <strong style={{ color: "var(--vcis-text)" }}>{assignmentCount}</strong>
          </div>
          <div>
            <span style={{ color: "var(--vcis-text-muted)" }}>Academic Counselling: </span>
            <strong style={{ color: "var(--vcis-text)" }}>{counsellingCount}</strong>
          </div>
          <div>
            <span style={{ color: "var(--vcis-text-muted)" }}>Monitoring: </span>
            <strong style={{ color: "var(--vcis-text)" }}>{monitoringCount}</strong>
          </div>
        </div>

        {/* Filter and Search Controls */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "var(--space-3)",
            marginBottom: "var(--space-4)",
          }}
        >
          <div style={{ flex: 1, minWidth: "240px" }}>
            <input
              id="admin-intervention-search-input"
              type="text"
              placeholder="Filter by student, faculty, or plan..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="vcis-input"
            />
          </div>

          <div style={{ width: "160px" }}>
            <select
              id="admin-intervention-status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="vcis-select"
            >
              <option value="all">All Statuses</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </div>

          <div style={{ width: "180px" }}>
            <select
              id="admin-intervention-type-filter"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="vcis-select"
            >
              <option value="all">All Types</option>
              <option value="extra_class">Extra Class</option>
              <option value="additional_assignment">Assignment</option>
              <option value="counselling">Counselling</option>
              <option value="monitoring">Monitoring</option>
            </select>
          </div>
        </div>

        {updateError && (
          <div className="vcis-alert vcis-alert-danger" style={{ marginBottom: "var(--space-4)" }}>
            ✕ {updateError}
          </div>
        )}

        {/* Comprehensive Interventions Table */}
        {isLoading ? (
          <div style={{ padding: "var(--space-8)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
            Loading intervention records...
          </div>
        ) : filteredInterventions.length === 0 ? (
          <div
            style={{
              padding: "var(--space-8)",
              textAlign: "center",
              backgroundColor: "var(--vcis-surface-soft)",
              borderRadius: "var(--radius-md)",
              border: "1px dashed var(--vcis-border-strong)",
              color: "var(--vcis-text-muted)",
              fontSize: "var(--vcis-font-size-sm)",
            }}
          >
            No intervention records match the selected filters.
          </div>
        ) : (
          <div className="vcis-table-wrapper" style={{ maxHeight: "420px" }}>
            <table className="vcis-table">
              <thead className="vcis-table-header">
                <tr>
                  <th style={{ width: "70px" }}>ID</th>
                  <th>Student</th>
                  <th>Assigned Faculty</th>
                  <th>Type</th>
                  <th style={{ width: "130px" }}>Status</th>
                  <th style={{ width: "80px" }}>Sem</th>
                  <th>Trigger Evidence</th>
                  <th>Action Plan</th>
                  <th style={{ width: "110px" }}>Created</th>
                  <th style={{ width: "110px" }}>Follow-up</th>
                  {onUpdateIntervention && (
                    <th style={{ width: "120px", textAlign: "right" }}>Actions</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {filteredInterventions.map((item) => {
                  const isEditing = editingId === item.id;
                  const statusBadgeClass = getStatusBadgeClass(item.status);
                  const studentLabel = studentMap.get(item.student_id) || `Student #${item.student_id}`;
                  const facultyLabel = facultyMap.get(item.faculty_id) || `Faculty #${item.faculty_id}`;

                  return (
                    <tr
                      key={item.id}
                      className="vcis-table-row"
                      style={{
                        backgroundColor: isEditing ? "var(--vcis-surface-soft)" : undefined,
                      }}
                    >
                      <td className="vcis-table-cell" style={{ fontWeight: 600, color: "var(--vcis-text-muted)" }}>
                        #{item.id}
                      </td>
                      <td className="vcis-table-cell" style={{ fontWeight: 600, color: "var(--vcis-text)" }}>
                        {studentLabel}
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-secondary)" }}>
                        {facultyLabel}
                      </td>
                      <td className="vcis-table-cell" style={{ fontWeight: 500, color: "var(--vcis-text)" }}>
                        {formatType(item.intervention_type)}
                      </td>
                      <td className="vcis-table-cell">
                        {isEditing ? (
                          <select
                            value={newStatus}
                            onChange={(e) => setNewStatus(e.target.value)}
                            className="vcis-select"
                            style={{ minHeight: "30px", padding: "0.2rem 0.5rem", fontSize: "var(--vcis-font-size-xs)" }}
                          >
                            <option value="assigned">Assigned</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                            <option value="dismissed">Dismissed</option>
                          </select>
                        ) : (
                          <span className={`vcis-badge ${statusBadgeClass}`}>
                            {item.status.replace("_", " ")}
                          </span>
                        )}
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-secondary)" }}>
                        Sem {item.semester}
                      </td>
                      <td className="vcis-table-cell" style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-secondary)" }}>
                        {item.trigger_predicted_score !== null && item.trigger_predicted_score !== undefined ? (
                          <>
                            <strong>{item.trigger_predicted_score.toFixed(2)}%</strong>{" "}
                            <span
                              style={{
                                fontSize: "0.72rem",
                                color:
                                  item.trigger_academic_status === "INTERVENTION"
                                    ? "var(--vcis-danger)"
                                    : item.trigger_academic_status === "MONITOR"
                                    ? "var(--vcis-warning)"
                                    : "var(--vcis-success)",
                              }}
                            >
                              ({item.trigger_academic_status})
                            </span>
                          </>
                        ) : (
                          "None recorded"
                        )}
                      </td>
                      <td className="vcis-table-cell" style={{ maxWidth: "220px" }}>
                        {isEditing ? (
                          <input
                            type="text"
                            value={newActionPlan}
                            onChange={(e) => setNewActionPlan(e.target.value)}
                            className="vcis-input"
                            style={{ minHeight: "30px", padding: "0.2rem 0.5rem", fontSize: "var(--vcis-font-size-xs)" }}
                          />
                        ) : (
                          <span style={{ color: "var(--vcis-text)", fontSize: "var(--vcis-font-size-xs)" }}>
                            {item.action_plan}
                          </span>
                        )}
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-muted)", fontSize: "var(--vcis-font-size-xs)" }}>
                        {formatDate(item.created_at)}
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-muted)", fontSize: "var(--vcis-font-size-xs)" }}>
                        {isEditing ? (
                          <input
                            type="date"
                            value={newFollowUpDate}
                            onChange={(e) => setNewFollowUpDate(e.target.value)}
                            className="vcis-input"
                            style={{ minHeight: "30px", padding: "0.2rem 0.5rem", fontSize: "var(--vcis-font-size-xs)" }}
                          />
                        ) : (
                          formatDate(item.follow_up_date)
                        )}
                      </td>
                      {onUpdateIntervention && (
                        <td className="vcis-table-cell" style={{ textAlign: "right" }}>
                          {isEditing ? (
                            <div style={{ display: "flex", gap: "var(--space-1)", justifyContent: "flex-end" }}>
                              <button
                                onClick={() => handleSave(item.id)}
                                disabled={isSaving}
                                className="vcis-btn vcis-btn-primary vcis-btn-sm"
                              >
                                Save
                              </button>
                              <button
                                onClick={cancelEdit}
                                disabled={isSaving}
                                className="vcis-btn vcis-btn-secondary vcis-btn-sm"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => startEdit(item)}
                              className="vcis-btn vcis-btn-secondary vcis-btn-sm"
                            >
                              Update
                            </button>
                          )}
                        </td>
                      )}
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

export default AdminInterventionOverview;
