import React, { useState, useMemo } from "react";
import type { FacultyProfile } from "../../api/facultyApi";
import { updateFacultyProfile, createFacultyProfile } from "../../api/facultyApi";
import type { DepartmentInfo } from "../../api/studentApi";
import type { UserResponse } from "../../api/adminApi";

interface AdminFacultyDirectoryProps {
  faculty: FacultyProfile[];
  departments: DepartmentInfo[];
  isLoading: boolean;
  users?: UserResponse[];
  onFacultyUpdated?: () => void;
}

export const AdminFacultyDirectory: React.FC<AdminFacultyDirectoryProps> = ({
  faculty,
  departments,
  isLoading,
  users = [],
  onFacultyUpdated,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [deptFilter, setDeptFilter] = useState<string>("all");
  const [roleFilter, setRoleFilter] = useState<string>("all");

  // Inline department assignment state per faculty record
  const [selectedDepts, setSelectedDepts] = useState<Record<number, number>>({});
  const [savingId, setSavingId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<{
    id: number;
    type: "success" | "error";
    message: string;
  } | null>(null);

  // Unassigned HOD user assignment state
  const [unassignedDeptSelections, setUnassignedDeptSelections] = useState<
    Record<number, number>
  >({});
  const [isSubmittingUnassigned, setIsSubmittingUnassigned] = useState<number | null>(
    null
  );
  const [unassignedFeedback, setUnassignedFeedback] = useState<{
    id: number;
    type: "success" | "error";
    message: string;
  } | null>(null);

  const deptMap = useMemo(() => {
    const map = new Map<number, string>();
    departments.forEach((d) => map.set(d.id, d.code || d.name));
    return map;
  }, [departments]);

  const activeDepartments = useMemo(() => {
    return departments.filter((d) => d.is_active !== false);
  }, [departments]);

  const userRoleMap = useMemo(() => {
    const map = new Map<number, string>();
    users.forEach((u) => map.set(u.id, u.role));
    return map;
  }, [users]);

  // HOD accounts provisioned in users but not yet having a faculty profile
  const unassignedHodUsers = useMemo(() => {
    return users.filter(
      (u) => u.role === "hod" && !faculty.some((f) => f.user_id === u.id)
    );
  }, [users, faculty]);

  const filteredFaculty = useMemo(() => {
    return faculty.filter((f) => {
      const fullName = `${f.first_name} ${f.last_name}`.toLowerCase();
      const matchesSearch =
        fullName.includes(searchTerm.toLowerCase()) ||
        f.employee_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.designation.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesDept =
        deptFilter === "all" || f.department_id === Number(deptFilter);

      const userRole = userRoleMap.get(f.user_id);
      const isHod = userRole === "hod";
      const matchesRole =
        roleFilter === "all" ||
        (roleFilter === "hod" && isHod) ||
        (roleFilter === "faculty" && !isHod);

      return matchesSearch && matchesDept && matchesRole;
    });
  }, [faculty, searchTerm, deptFilter, roleFilter, userRoleMap]);

  const handleSaveDepartment = async (f: FacultyProfile) => {
    const chosenDeptId = selectedDepts[f.id];
    if (!chosenDeptId || chosenDeptId === 0) return;

    setSavingId(f.id);
    setFeedback(null);

    try {
      await updateFacultyProfile(f.id, {
        department_id: chosenDeptId,
        employee_code: f.employee_code,
        first_name: f.first_name,
        last_name: f.last_name,
        designation: f.designation,
        phone: f.phone,
        is_active: f.is_active,
      });

      setFeedback({
        id: f.id,
        type: "success",
        message: "Department assigned successfully.",
      });

      if (onFacultyUpdated) {
        onFacultyUpdated();
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to update department.";
      setFeedback({
        id: f.id,
        type: "error",
        message: msg,
      });
    } finally {
      setSavingId(null);
    }
  };

  const handleAssignUnassignedHod = async (u: UserResponse) => {
    const chosenDeptId = unassignedDeptSelections[u.id];
    if (!chosenDeptId || chosenDeptId === 0) return;

    setIsSubmittingUnassigned(u.id);
    setUnassignedFeedback(null);

    try {
      const rawPrefix = u.email.split("@")[0].toUpperCase().replace(/[^A-Z0-9]/g, "");
      const employeeCode = `HOD-${rawPrefix || "USER"}-${u.id}`;

      await createFacultyProfile({
        user_id: u.id,
        department_id: chosenDeptId,
        employee_code: employeeCode.slice(0, 30),
        first_name: "Head of",
        last_name: "Department",
        designation: "Head of Department",
      });

      setUnassignedFeedback({
        id: u.id,
        type: "success",
        message: "HOD faculty profile created and department assigned.",
      });

      if (onFacultyUpdated) {
        onFacultyUpdated();
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to assign department.";
      setUnassignedFeedback({
        id: u.id,
        type: "error",
        message: msg,
      });
    } finally {
      setIsSubmittingUnassigned(null);
    }
  };

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)" }}>
      {/* Header */}
      <div className="vcis-card-header">
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: "var(--vcis-font-size-md)",
              fontWeight: "var(--vcis-font-weight-semibold)",
              color: "var(--vcis-text)",
            }}
          >
            Institutional Faculty & HOD Directory
          </h3>
          <p
            style={{
              margin: "var(--space-1) 0 0 0",
              fontSize: "var(--vcis-font-size-xs)",
              color: "var(--vcis-text-muted)",
            }}
          >
            Registered professors, academic instructors, and department heads
          </p>
        </div>
        <span
          style={{
            fontSize: "var(--vcis-font-size-xs)",
            color: "var(--vcis-text-muted)",
          }}
        >
          Showing {filteredFaculty.length} of {faculty.length} faculty
        </span>
      </div>

      <div className="vcis-card-body">
        {/* Unassigned HOD Users Callout (if any) */}
        {unassignedHodUsers.length > 0 && (
          <div
            className="vcis-card"
            style={{
              marginBottom: "var(--space-4)",
              border: "1px solid var(--vcis-warning, #f59e0b)",
              backgroundColor: "var(--vcis-surface-soft)",
            }}
          >
            <div
              style={{
                padding: "var(--space-3) var(--space-4)",
                borderBottom: "1px solid var(--vcis-border-soft)",
              }}
            >
              <h4
                style={{
                  margin: 0,
                  fontSize: "var(--vcis-font-size-sm)",
                  color: "var(--vcis-text)",
                  fontWeight: 600,
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-2)",
                }}
              >
                <span>⚠️</span> Unassigned HOD User Accounts ({unassignedHodUsers.length})
              </h4>
              <p
                style={{
                  margin: "2px 0 0 0",
                  fontSize: "var(--vcis-font-size-xs)",
                  color: "var(--vcis-text-muted)",
                }}
              >
                These HOD accounts have been provisioned but do not yet have a department assignment. Assign a department to activate their academic governance scope.
              </p>
            </div>
            <div style={{ padding: "var(--space-3) var(--space-4)" }}>
              {unassignedHodUsers.map((u) => (
                <div
                  key={u.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "var(--space-2) 0",
                    borderTop: "1px solid var(--vcis-border-subtle)",
                    gap: "var(--space-3)",
                    flexWrap: "wrap",
                  }}
                >
                  <div>
                    <span
                      style={{
                        fontWeight: 600,
                        fontSize: "var(--vcis-font-size-sm)",
                        color: "var(--vcis-text)",
                      }}
                    >
                      {u.email}
                    </span>
                    <span
                      className="vcis-badge vcis-badge-primary"
                      style={{
                        marginLeft: "var(--space-2)",
                        fontSize: "10px",
                        padding: "1px 6px",
                      }}
                    >
                      HOD
                    </span>
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "var(--space-2)",
                    }}
                  >
                    <select
                      id={`unassigned-hod-dept-select-${u.id}`}
                      className="vcis-select"
                      style={{
                        padding: "4px 8px",
                        fontSize: "12px",
                        height: "30px",
                        minWidth: "180px",
                      }}
                      value={unassignedDeptSelections[u.id] || 0}
                      onChange={(e) =>
                        setUnassignedDeptSelections({
                          ...unassignedDeptSelections,
                          [u.id]: Number(e.target.value),
                        })
                      }
                      disabled={isSubmittingUnassigned === u.id}
                    >
                      <option value={0}>Select department</option>
                      {activeDepartments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.code})
                        </option>
                      ))}
                    </select>

                    <button
                      id={`unassigned-hod-assign-btn-${u.id}`}
                      className="vcis-btn vcis-btn-primary"
                      style={{
                        padding: "4px 12px",
                        fontSize: "12px",
                        height: "30px",
                      }}
                      disabled={
                        !unassignedDeptSelections[u.id] ||
                        unassignedDeptSelections[u.id] === 0 ||
                        isSubmittingUnassigned === u.id
                      }
                      onClick={() => handleAssignUnassignedHod(u)}
                    >
                      {isSubmittingUnassigned === u.id ? "Assigning..." : "Assign"}
                    </button>
                  </div>

                  {unassignedFeedback && unassignedFeedback.id === u.id && (
                    <div
                      style={{
                        width: "100%",
                        fontSize: "11px",
                        color:
                          unassignedFeedback.type === "success"
                            ? "var(--vcis-success, #10b981)"
                            : "var(--vcis-danger, #ef4444)",
                        fontWeight: 500,
                        marginTop: "2px",
                      }}
                    >
                      {unassignedFeedback.type === "success" ? "✓ " : "✕ "}
                      {unassignedFeedback.message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Filter Controls */}
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
              id="admin-faculty-search-input"
              type="text"
              placeholder="Filter by name, employee code, designation..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="vcis-input"
            />
          </div>

          <div style={{ width: "160px" }}>
            <select
              id="admin-faculty-role-filter"
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="vcis-select"
            >
              <option value="all">All Roles</option>
              <option value="hod">HODs Only</option>
              <option value="faculty">Faculty Only</option>
            </select>
          </div>

          <div style={{ width: "220px" }}>
            <select
              id="admin-faculty-dept-filter"
              value={deptFilter}
              onChange={(e) => setDeptFilter(e.target.value)}
              className="vcis-select"
            >
              <option value="all">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div
            style={{
              padding: "var(--space-8)",
              textAlign: "center",
              color: "var(--vcis-text-muted)",
            }}
          >
            Loading faculty directory...
          </div>
        ) : filteredFaculty.length === 0 ? (
          <div
            style={{
              padding: "var(--space-8)",
              textAlign: "center",
              color: "var(--vcis-text-muted)",
              fontSize: "var(--vcis-font-size-sm)",
              backgroundColor: "var(--vcis-surface-soft)",
              borderRadius: "var(--radius-md)",
              border: "1px dashed var(--vcis-border-strong)",
            }}
          >
            No faculty members match the current criteria.
          </div>
        ) : (
          <div className="vcis-table-wrapper" style={{ maxHeight: "460px" }}>
            <table className="vcis-table">
              <thead className="vcis-table-header">
                <tr>
                  <th style={{ width: "130px" }}>Employee Code</th>
                  <th>Faculty Name</th>
                  <th style={{ minWidth: "240px" }}>Department</th>
                  <th>Designation</th>
                  <th>Contact Phone</th>
                  <th style={{ width: "100px", textAlign: "right" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredFaculty.map((f) => {
                  const userRole = userRoleMap.get(f.user_id);
                  const isHod = userRole === "hod";
                  const currentDept = departments.find(
                    (d) => d.id === f.department_id
                  );
                  const isUnassigned = !currentDept;
                  const selectedDeptId =
                    selectedDepts[f.id] !== undefined
                      ? selectedDepts[f.id]
                      : currentDept
                      ? f.department_id
                      : 0;

                  return (
                    <tr key={f.id} className="vcis-table-row">
                      <td
                        className="vcis-table-cell"
                        style={{ fontWeight: 600, color: "var(--vcis-text)" }}
                      >
                        {f.employee_code}
                      </td>
                      <td
                        className="vcis-table-cell"
                        style={{ fontWeight: 500, color: "var(--vcis-text)" }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "var(--space-2)",
                          }}
                        >
                          <span>
                            {f.first_name} {f.last_name}
                          </span>
                          {isHod && (
                            <span
                              className="vcis-badge vcis-badge-primary"
                              style={{
                                fontSize: "10px",
                                fontWeight: 700,
                                padding: "1px 5px",
                                textTransform: "uppercase",
                                letterSpacing: "0.05em",
                              }}
                            >
                              HOD
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="vcis-table-cell">
                        {isHod ? (
                          <div
                            style={{
                              display: "flex",
                              flexDirection: "column",
                              gap: "4px",
                            }}
                          >
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "6px",
                              }}
                            >
                              <select
                                id={`hod-dept-select-${f.id}`}
                                value={selectedDeptId}
                                onChange={(e) => {
                                  const val = Number(e.target.value);
                                  setSelectedDepts((prev) => ({
                                    ...prev,
                                    [f.id]: val,
                                  }));
                                  setFeedback((prev) =>
                                    prev?.id === f.id ? null : prev
                                  );
                                }}
                                className="vcis-select"
                                style={{
                                  padding: "4px 8px",
                                  fontSize: "12px",
                                  height: "30px",
                                  flex: 1,
                                  minWidth: "140px",
                                }}
                                disabled={savingId === f.id}
                              >
                                {isUnassigned && (
                                  <option value={0}>Select department</option>
                                )}
                                {activeDepartments.map((d) => (
                                  <option key={d.id} value={d.id}>
                                    {d.name} ({d.code})
                                  </option>
                                ))}
                              </select>
                              <button
                                id={`hod-dept-save-btn-${f.id}`}
                                onClick={() => handleSaveDepartment(f)}
                                disabled={
                                  savingId === f.id ||
                                  (selectedDepts[f.id] === undefined &&
                                    !isUnassigned) ||
                                  selectedDeptId === f.department_id ||
                                  selectedDeptId === 0
                                }
                                className="vcis-btn vcis-btn-primary"
                                style={{
                                  padding: "4px 10px",
                                  fontSize: "12px",
                                  height: "30px",
                                  whiteSpace: "nowrap",
                                }}
                              >
                                {savingId === f.id
                                  ? "Saving..."
                                  : isUnassigned
                                  ? "Assign"
                                  : "Save"}
                              </button>
                            </div>
                            {feedback && feedback.id === f.id && (
                              <span
                                id={`hod-dept-feedback-${f.id}`}
                                style={{
                                  fontSize: "11px",
                                  color:
                                    feedback.type === "success"
                                      ? "var(--vcis-success, #10b981)"
                                      : "var(--vcis-danger, #ef4444)",
                                  fontWeight: 500,
                                }}
                              >
                                {feedback.type === "success" ? "✓ " : "✕ "}
                                {feedback.message}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: "var(--vcis-text-secondary)" }}>
                            {deptMap.get(f.department_id) ||
                              `Dept #${f.department_id}`}
                          </span>
                        )}
                      </td>
                      <td
                        className="vcis-table-cell"
                        style={{ color: "var(--vcis-text-secondary)" }}
                      >
                        {f.designation}
                      </td>
                      <td
                        className="vcis-table-cell"
                        style={{ color: "var(--vcis-text-muted)" }}
                      >
                        {f.phone || "Not recorded"}
                      </td>
                      <td
                        className="vcis-table-cell"
                        style={{ textAlign: "right" }}
                      >
                        <span
                          className={`vcis-badge ${
                            f.is_active
                              ? "vcis-badge-success"
                              : "vcis-badge-danger"
                          }`}
                        >
                          {f.is_active ? "Active" : "Inactive"}
                        </span>
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

export default AdminFacultyDirectory;
