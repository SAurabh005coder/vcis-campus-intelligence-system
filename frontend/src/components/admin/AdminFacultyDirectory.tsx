import React, { useState, useMemo } from "react";
import type { FacultyProfile } from "../../api/facultyApi";
import type { DepartmentInfo } from "../../api/studentApi";

interface AdminFacultyDirectoryProps {
  faculty: FacultyProfile[];
  departments: DepartmentInfo[];
  isLoading: boolean;
}

export const AdminFacultyDirectory: React.FC<AdminFacultyDirectoryProps> = ({
  faculty,
  departments,
  isLoading,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [deptFilter, setDeptFilter] = useState<string>("all");

  const deptMap = useMemo(() => {
    const map = new Map<number, string>();
    departments.forEach((d) => map.set(d.id, d.code || d.name));
    return map;
  }, [departments]);

  const filteredFaculty = useMemo(() => {
    return faculty.filter((f) => {
      const fullName = `${f.first_name} ${f.last_name}`.toLowerCase();
      const matchesSearch =
        fullName.includes(searchTerm.toLowerCase()) ||
        f.employee_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.designation.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesDept = deptFilter === "all" || f.department_id === Number(deptFilter);

      return matchesSearch && matchesDept;
    });
  }, [faculty, searchTerm, deptFilter]);

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)" }}>
      {/* Header */}
      <div className="vcis-card-header">
        <div>
          <h3 style={{ margin: 0, fontSize: "var(--vcis-font-size-md)", fontWeight: "var(--vcis-font-weight-semibold)", color: "var(--vcis-text)" }}>
            Institutional Faculty Directory
          </h3>
          <p style={{ margin: "var(--space-1) 0 0 0", fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
            Registered professors, academic instructors, and department heads
          </p>
        </div>
        <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
          Showing {filteredFaculty.length} of {faculty.length} faculty
        </span>
      </div>

      <div className="vcis-card-body">
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
          <div style={{ padding: "var(--space-8)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
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
          <div className="vcis-table-wrapper" style={{ maxHeight: "380px" }}>
            <table className="vcis-table">
              <thead className="vcis-table-header">
                <tr>
                  <th style={{ width: "130px" }}>Employee Code</th>
                  <th>Faculty Name</th>
                  <th>Department</th>
                  <th>Designation</th>
                  <th>Contact Phone</th>
                  <th style={{ width: "100px", textAlign: "right" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredFaculty.map((f) => (
                  <tr key={f.id} className="vcis-table-row">
                    <td className="vcis-table-cell" style={{ fontWeight: 600, color: "var(--vcis-text)" }}>
                      {f.employee_code}
                    </td>
                    <td className="vcis-table-cell" style={{ fontWeight: 500, color: "var(--vcis-text)" }}>
                      {f.first_name} {f.last_name}
                    </td>
                    <td className="vcis-table-cell" style={{ color: "var(--vcis-text-secondary)" }}>
                      {deptMap.get(f.department_id) || `Dept #${f.department_id}`}
                    </td>
                    <td className="vcis-table-cell" style={{ color: "var(--vcis-text-secondary)" }}>
                      {f.designation}
                    </td>
                    <td className="vcis-table-cell" style={{ color: "var(--vcis-text-muted)" }}>
                      {f.phone || "Not recorded"}
                    </td>
                    <td className="vcis-table-cell" style={{ textAlign: "right" }}>
                      <span
                        className={`vcis-badge ${f.is_active ? "vcis-badge-success" : "vcis-badge-danger"}`}
                      >
                        {f.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminFacultyDirectory;
