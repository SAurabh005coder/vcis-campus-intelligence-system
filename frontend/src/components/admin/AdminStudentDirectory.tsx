import React, { useState, useMemo } from "react";
import type { StudentProfile, DepartmentInfo, CourseInfo } from "../../api/studentApi";

interface AdminStudentDirectoryProps {
  students: StudentProfile[];
  departments: DepartmentInfo[];
  courses: CourseInfo[];
  selectedStudent: StudentProfile | null;
  onSelectStudent: (student: StudentProfile) => void;
  isLoading: boolean;
}

export const AdminStudentDirectory: React.FC<AdminStudentDirectoryProps> = ({
  students,
  departments,
  courses,
  selectedStudent,
  onSelectStudent,
  isLoading,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [deptFilter, setDeptFilter] = useState<string>("all");
  const [semFilter, setSemFilter] = useState<string>("all");

  const deptMap = useMemo(() => {
    const map = new Map<number, string>();
    departments.forEach((d) => map.set(d.id, d.code || d.name));
    return map;
  }, [departments]);

  const courseMap = useMemo(() => {
    const map = new Map<number, string>();
    courses.forEach((c) => map.set(c.id, c.code || c.name));
    return map;
  }, [courses]);

  const filteredStudents = useMemo(() => {
    return students.filter((s) => {
      const matchesSearch =
        s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.roll_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.email.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesDept = deptFilter === "all" || s.department_id === Number(deptFilter);
      const matchesSem = semFilter === "all" || s.current_semester === Number(semFilter);

      return matchesSearch && matchesDept && matchesSem;
    });
  }, [students, searchTerm, deptFilter, semFilter]);

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)" }}>
      {/* Header */}
      <div className="vcis-card-header">
        <div>
          <h3 style={{ margin: 0, fontSize: "var(--vcis-font-size-md)", fontWeight: "var(--vcis-font-weight-semibold)", color: "var(--vcis-text)" }}>
            Institutional Student Directory
          </h3>
          <p style={{ margin: "var(--space-1) 0 0 0", fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
            Comprehensive register of enrolled students across all departments
          </p>
        </div>
        <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
          Showing {filteredStudents.length} of {students.length} students
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
              id="admin-student-search-input"
              type="text"
              placeholder="Filter by name, roll no, email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="vcis-input"
            />
          </div>

          <div style={{ width: "200px" }}>
            <select
              id="admin-student-dept-filter"
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

          <div style={{ width: "160px" }}>
            <select
              id="admin-student-sem-filter"
              value={semFilter}
              onChange={(e) => setSemFilter(e.target.value)}
              className="vcis-select"
            >
              <option value="all">All Semesters</option>
              <option value="1">Semester 1</option>
              <option value="2">Semester 2</option>
              <option value="3">Semester 3</option>
              <option value="4">Semester 4</option>
            </select>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div style={{ padding: "var(--space-8)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
            Loading student directory...
          </div>
        ) : filteredStudents.length === 0 ? (
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
            No students match the current criteria.
          </div>
        ) : (
          <div className="vcis-table-wrapper" style={{ maxHeight: "380px" }}>
            <table className="vcis-table">
              <thead className="vcis-table-header">
                <tr>
                  <th style={{ width: "120px" }}>Roll No</th>
                  <th>Student Name</th>
                  <th>Department</th>
                  <th>Course</th>
                  <th style={{ width: "100px" }}>Semester</th>
                  <th style={{ width: "110px" }}>Admission</th>
                  <th style={{ width: "100px" }}>Status</th>
                  <th style={{ width: "110px", textAlign: "right" }}>Action</th>
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
                      <td className="vcis-table-cell" style={{ fontWeight: 600, color: "var(--vcis-text)" }}>
                        {s.roll_number}
                      </td>
                      <td className="vcis-table-cell" style={{ fontWeight: 500, color: "var(--vcis-text)" }}>
                        {s.name}
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-secondary)" }}>
                        {deptMap.get(s.department_id) || `Dept #${s.department_id}`}
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-secondary)" }}>
                        {courseMap.get(s.course_id) || `Course #${s.course_id}`}
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-secondary)" }}>
                        Sem {s.current_semester}
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-muted)" }}>
                        {s.admission_year}
                      </td>
                      <td className="vcis-table-cell">
                        <span
                          className={`vcis-badge ${s.is_active ? "vcis-badge-success" : "vcis-badge-danger"}`}
                        >
                          {s.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="vcis-table-cell" style={{ textAlign: "right" }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectStudent(s);
                          }}
                          className={`vcis-btn vcis-btn-sm ${isSelected ? "vcis-btn-primary" : "vcis-btn-secondary"}`}
                        >
                          {isSelected ? "Inspecting" : "Inspect"}
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

export default AdminStudentDirectory;
