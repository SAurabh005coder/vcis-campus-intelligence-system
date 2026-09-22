import React, { useState } from "react";
import type { DepartmentInfo, CourseInfo, StudentProfile } from "../../api/studentApi";
import type { FacultyProfile } from "../../api/facultyApi";
import type { SubjectInfo } from "../../api/adminApi";

interface AcademicStructureOverviewProps {
  departments: DepartmentInfo[];
  courses: CourseInfo[];
  subjects: SubjectInfo[];
  students: StudentProfile[];
  faculty: FacultyProfile[];
}

export const AcademicStructureOverview: React.FC<AcademicStructureOverviewProps> = ({
  departments,
  courses,
  subjects,
  students,
  faculty,
}) => {
  const [selectedDeptId, setSelectedDeptId] = useState<number | "all">("all");

  // Compute department-specific metrics
  const deptMetrics = departments.map((dept) => {
    const deptCourses = courses.filter((c) => c.department_id === dept.id);
    const deptCourseIds = new Set(deptCourses.map((c) => c.id));
    const deptSubjects = subjects.filter((s) => deptCourseIds.has(s.course_id));
    const deptStudents = students.filter((s) => s.department_id === dept.id);
    const deptFaculty = faculty.filter((f) => f.department_id === dept.id);

    return {
      dept,
      coursesCount: deptCourses.length,
      subjectsCount: deptSubjects.length,
      studentsCount: deptStudents.length,
      facultyCount: deptFaculty.length,
    };
  });

  const filteredCourses =
    selectedDeptId === "all"
      ? courses
      : courses.filter((c) => c.department_id === selectedDeptId);

  const deptMap = new Map<number, string>();
  departments.forEach((d) => deptMap.set(d.id, `${d.name} (${d.code})`));

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)" }}>
      {/* Header */}
      <div className="vcis-card-header">
        <div>
          <h3 style={{ margin: 0, fontSize: "var(--vcis-font-size-md)", fontWeight: "var(--vcis-font-weight-semibold)", color: "var(--vcis-text)" }}>
            Academic Structure & Institutional Hierarchy
          </h3>
          <p style={{ margin: "var(--space-1) 0 0 0", fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
            Departments, academic degree courses, and curriculum coursework
          </p>
        </div>

        <div style={{ minWidth: "240px" }}>
          <select
            id="admin-structure-dept-filter"
            value={selectedDeptId}
            onChange={(e) =>
              setSelectedDeptId(e.target.value === "all" ? "all" : Number(e.target.value))
            }
            className="vcis-select"
          >
            <option value="all">All Departments ({departments.length})</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.code})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="vcis-card-body">
        {/* Department Breakdown Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "var(--space-4)",
            marginBottom: "var(--space-6)",
          }}
        >
          {deptMetrics
            .filter((m) => selectedDeptId === "all" || m.dept.id === selectedDeptId)
            .map(({ dept, coursesCount, subjectsCount, studentsCount, facultyCount }) => (
              <div
                key={dept.id}
                style={{
                  backgroundColor: "var(--vcis-surface-soft)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--vcis-border)",
                  padding: "var(--space-4)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "var(--space-2)",
                    }}
                  >
                    <div>
                      <h4 style={{ margin: 0, fontSize: "var(--vcis-font-size-sm)", fontWeight: "var(--vcis-font-weight-bold)", color: "var(--vcis-text)" }}>
                        {dept.name}
                      </h4>
                      <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
                        Code: {dept.code}
                      </span>
                    </div>
                    <span
                      className={`vcis-badge ${dept.is_active ? "vcis-badge-success" : "vcis-badge-danger"}`}
                    >
                      {dept.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>

                  {dept.description && (
                    <p style={{ margin: "0 0 var(--space-3) 0", fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-secondary)", lineHeight: 1.4 }}>
                      {dept.description}
                    </p>
                  )}
                </div>

                {/* Metric Summary Grid */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(4, 1fr)",
                    gap: "var(--space-2)",
                    backgroundColor: "var(--vcis-surface)",
                    padding: "var(--space-2) var(--space-3)",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--vcis-border)",
                    textAlign: "center",
                    fontSize: "var(--vcis-font-size-xs)",
                    marginTop: "var(--space-3)",
                  }}
                >
                  <div>
                    <span style={{ color: "var(--vcis-text-muted)", display: "block", fontSize: "0.68rem" }}>Courses</span>
                    <strong style={{ color: "var(--vcis-text)", fontSize: "var(--vcis-font-size-sm)" }}>{coursesCount}</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--vcis-text-muted)", display: "block", fontSize: "0.68rem" }}>Subjects</span>
                    <strong style={{ color: "var(--vcis-accent)", fontSize: "var(--vcis-font-size-sm)" }}>{subjectsCount}</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--vcis-text-muted)", display: "block", fontSize: "0.68rem" }}>Students</span>
                    <strong style={{ color: "var(--vcis-primary)", fontSize: "var(--vcis-font-size-sm)" }}>{studentsCount}</strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--vcis-text-muted)", display: "block", fontSize: "0.68rem" }}>Faculty</span>
                    <strong style={{ color: "var(--vcis-success)", fontSize: "var(--vcis-font-size-sm)" }}>{facultyCount}</strong>
                  </div>
                </div>
              </div>
            ))}
        </div>

        {/* Degree Programs & Courses Table */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
            <h4
              style={{
                margin: 0,
                fontSize: "var(--vcis-font-size-sm)",
                fontWeight: "var(--vcis-font-weight-semibold)",
                color: "var(--vcis-text)",
              }}
            >
              Active Degree Programs & Courses ({filteredCourses.length})
            </h4>
            <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
              Official Institutional Catalog
            </span>
          </div>

          {filteredCourses.length === 0 ? (
            <div
              style={{
                padding: "var(--space-6)",
                backgroundColor: "var(--vcis-surface-soft)",
                borderRadius: "var(--radius-md)",
                border: "1px dashed var(--vcis-border-strong)",
                color: "var(--vcis-text-muted)",
                fontSize: "var(--vcis-font-size-sm)",
                textAlign: "center",
              }}
            >
              No courses found for the selected department.
            </div>
          ) : (
            <div className="vcis-table-wrapper" style={{ maxHeight: "300px" }}>
              <table className="vcis-table">
                <thead className="vcis-table-header">
                  <tr>
                    <th>Code</th>
                    <th>Course Name</th>
                    <th>Department</th>
                    <th>Duration</th>
                    <th>Total Semesters</th>
                    <th style={{ textAlign: "right" }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCourses.map((c) => (
                    <tr key={c.id} className="vcis-table-row">
                      <td className="vcis-table-cell" style={{ fontWeight: 600, color: "var(--vcis-primary)" }}>
                        {c.code}
                      </td>
                      <td className="vcis-table-cell" style={{ fontWeight: 500, color: "var(--vcis-text)" }}>
                        {c.name}
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-secondary)" }}>
                        {deptMap.get(c.department_id) || `Dept #${c.department_id}`}
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-secondary)" }}>
                        {c.duration_years} Years
                      </td>
                      <td className="vcis-table-cell" style={{ color: "var(--vcis-text-secondary)" }}>
                        {c.total_semesters} Semesters
                      </td>
                      <td className="vcis-table-cell" style={{ textAlign: "right" }}>
                        <span
                          className={`vcis-badge ${c.is_active ? "vcis-badge-success" : "vcis-badge-danger"}`}
                        >
                          {c.is_active ? "Active" : "Inactive"}
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
    </div>
  );
};

export default AcademicStructureOverview;
