import React, { useState, useMemo } from "react";
import type { StudentProfile, DepartmentInfo } from "../../api/studentApi";

interface StudentSelectorProps {
  students: StudentProfile[];
  departments: DepartmentInfo[];
  facultyDepartmentId?: number | null;
  selectedStudent: StudentProfile | null;
  onSelectStudent: (student: StudentProfile) => void;
  isLoading: boolean;
}

export const StudentSelector: React.FC<StudentSelectorProps> = ({
  students,
  departments,
  facultyDepartmentId,
  selectedStudent,
  onSelectStudent,
  isLoading,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [semesterFilter, setSemesterFilter] = useState<string>("all");
  const [departmentFilter, setDepartmentFilter] = useState<string>("all");

  const deptMap = useMemo(() => {
    const map = new Map<number, string>();
    departments.forEach((d) => map.set(d.id, d.code || d.name));
    return map;
  }, [departments]);

  const filteredStudents = useMemo(() => {
    return students.filter((s) => {
      const matchSearch =
        s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.roll_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.email.toLowerCase().includes(searchTerm.toLowerCase());

      const matchSemester =
        semesterFilter === "all" || s.current_semester === Number(semesterFilter);

      let matchDepartment = true;
      if (departmentFilter === "my_dept") {
        matchDepartment = s.department_id === facultyDepartmentId;
      } else if (departmentFilter !== "all") {
        matchDepartment = s.department_id === Number(departmentFilter);
      }

      return matchSearch && matchSemester && matchDepartment;
    });
  }, [students, searchTerm, semesterFilter, departmentFilter, facultyDepartmentId]);

  return (
    <div className="vcis-card">
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Select Student</h3>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>
            Search student directory to review academic indicators & predictions
          </p>
        </div>
        <span
          className="vcis-status vcis-status-neutral"
          style={{ fontSize: "var(--font-xs)" }}
        >
          {filteredStudents.length} of {students.length} students
        </span>
      </div>

      <div className="vcis-card-body">
        {/* Search and Filters */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-3)",
            marginBottom: "var(--space-4)",
          }}
        >
          <div style={{ position: "relative" }}>
            <input
              type="text"
              placeholder="Search students by name, roll no, or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="vcis-input"
              style={{ width: "100%", paddingRight: "2rem" }}
              aria-label="Search students"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm("")}
                style={{
                  position: "absolute",
                  right: "0.75rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  color: "var(--vcis-text-muted)",
                  cursor: "pointer",
                  fontSize: "1rem",
                  padding: 0,
                }}
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "var(--space-2)",
            }}
          >
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="vcis-select"
              aria-label="Filter by department"
            >
              <option value="all">All Departments</option>
              {facultyDepartmentId && (
                <option value="my_dept">My Department</option>
              )}
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>

            <select
              value={semesterFilter}
              onChange={(e) => setSemesterFilter(e.target.value)}
              className="vcis-select"
              aria-label="Filter by semester"
            >
              <option value="all">All Semesters</option>
              <option value="1">Semester 1</option>
              <option value="2">Semester 2</option>
              <option value="3">Semester 3</option>
              <option value="4">Semester 4</option>
            </select>
          </div>
        </div>

        {/* Student Directory Table / List */}
        {isLoading ? (
          <div className="vcis-loading" style={{ padding: "var(--space-6) 0" }}>
            <div className="vcis-spinner" aria-hidden="true" />
            <span style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)" }}>
              Loading student directory...
            </span>
          </div>
        ) : filteredStudents.length === 0 ? (
          <div className="vcis-empty">
            No students match the criteria.
          </div>
        ) : (
          <div
            className="vcis-table-wrapper"
            style={{ maxHeight: "320px", overflowY: "auto" }}
          >
            <table className="vcis-table">
              <thead>
                <tr>
                  <th className="vcis-table-header">Roll No</th>
                  <th className="vcis-table-header">Name</th>
                  <th className="vcis-table-header">Dept</th>
                  <th className="vcis-table-header" style={{ textAlign: "center" }}>Sem</th>
                  <th className="vcis-table-header" style={{ textAlign: "right" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredStudents.map((s) => {
                  const isSelected = selectedStudent?.id === s.id;
                  return (
                    <tr
                      key={s.id}
                      onClick={() => onSelectStudent(s)}
                      className={`vcis-table-row ${isSelected ? "is-selected" : ""}`}
                      style={{ cursor: "pointer" }}
                    >
                      <td
                        className="vcis-table-cell"
                        style={{
                          fontWeight: isSelected
                            ? "var(--font-weight-bold)"
                            : "var(--font-weight-semibold)",
                          color: isSelected
                            ? "var(--vcis-primary-hover)"
                            : "var(--vcis-text)",
                        }}
                      >
                        {s.roll_number}
                      </td>
                      <td className="vcis-table-cell" style={{ fontWeight: "var(--font-weight-medium)" }}>
                        {s.name}
                      </td>
                      <td className="vcis-table-cell" style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-muted)" }}>
                        {deptMap.get(s.department_id) || `Dept #${s.department_id}`}
                      </td>
                      <td className="vcis-table-cell" style={{ textAlign: "center", fontSize: "var(--font-xs)" }}>
                        Sem {s.current_semester}
                      </td>
                      <td className="vcis-table-cell" style={{ textAlign: "right" }}>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectStudent(s);
                          }}
                          className={`vcis-button vcis-button-sm ${
                            isSelected ? "vcis-button-primary" : "vcis-button-secondary"
                          }`}
                          style={{ padding: "0.2rem 0.6rem", fontSize: "var(--font-xs)" }}
                        >
                          {isSelected ? "Selected" : "Select"}
                        </button>
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

export default StudentSelector;
