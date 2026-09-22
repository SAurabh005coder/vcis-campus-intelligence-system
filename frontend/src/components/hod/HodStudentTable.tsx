import React, { useState, useMemo } from "react";
import type { StudentProfile, DepartmentInfo } from "../../api/studentApi";
import type { InterventionResponse } from "../../api/interventionApi";

interface HodStudentTableProps {
  students: StudentProfile[];
  departments: DepartmentInfo[];
  interventions: InterventionResponse[];
  selectedStudent: StudentProfile | null;
  onSelectStudent: (student: StudentProfile) => void;
  isLoading: boolean;
}

export const HodStudentTable: React.FC<HodStudentTableProps> = ({
  students,
  departments,
  interventions,
  selectedStudent,
  onSelectStudent,
  isLoading,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [semesterFilter, setSemesterFilter] = useState<string>("all");

  const deptMap = useMemo(() => {
    const map = new Map<number, string>();
    departments.forEach((d) => map.set(d.id, d.code || d.name));
    return map;
  }, [departments]);

  // Count interventions per student_id
  const studentInterventionCount = useMemo(() => {
    const counts = new Map<number, number>();
    interventions.forEach((i) => {
      counts.set(i.student_id, (counts.get(i.student_id) || 0) + 1);
    });
    return counts;
  }, [interventions]);

  const filteredStudents = useMemo(() => {
    return students.filter((s) => {
      const matchSearch =
        s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.roll_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.email.toLowerCase().includes(searchTerm.toLowerCase());

      const matchSemester =
        semesterFilter === "all" || s.current_semester === Number(semesterFilter);

      return matchSearch && matchSemester;
    });
  }, [students, searchTerm, semesterFilter]);

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)" }}>
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Student Academic Overview</h3>
          <p className="vcis-card-subtitle">
            Department roster inspection, search discovery, and academic attention oversight
          </p>
        </div>
        <span className="vcis-badge vcis-badge-neutral">
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
          <input
            type="text"
            id="hod-student-search-input"
            aria-label="Filter students by name, roll number, or email"
            placeholder="Search by name, roll no, email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="vcis-form-input"
            style={{
              flex: 1,
              minWidth: "220px",
            }}
          />

          <select
            id="hod-semester-filter-select"
            aria-label="Filter students by semester"
            value={semesterFilter}
            onChange={(e) => setSemesterFilter(e.target.value)}
            className="vcis-form-select"
            style={{
              width: "auto",
              minWidth: "160px",
            }}
          >
            <option value="all">All Semesters</option>
            <option value="1">Semester 1</option>
            <option value="2">Semester 2</option>
            <option value="3">Semester 3</option>
            <option value="4">Semester 4</option>
          </select>
        </div>

        {/* Roster Table */}
        {isLoading ? (
          <div className="vcis-empty-state" style={{ padding: "var(--space-8)" }}>
            <p className="vcis-empty-text">Loading student roster...</p>
          </div>
        ) : filteredStudents.length === 0 ? (
          <div className="vcis-empty-state" style={{ padding: "var(--space-8)" }}>
            <p className="vcis-empty-title">No Students Found</p>
            <p className="vcis-empty-text">No students match the current search criteria or semester filter.</p>
          </div>
        ) : (
          <div
            className="vcis-table-wrapper"
            style={{
              maxHeight: "360px",
              overflowY: "auto",
            }}
          >
            <table className="vcis-table">
              <thead className="vcis-table-header">
                <tr>
                  <th>Roll No</th>
                  <th>Student Name</th>
                  <th>Dept</th>
                  <th>Semester</th>
                  <th>Interventions</th>
                  <th style={{ textAlign: "right" }}>Oversight Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredStudents.map((s) => {
                  const isSelected = selectedStudent?.id === s.id;
                  const intervCount = studentInterventionCount.get(s.id) || 0;

                  return (
                    <tr
                      key={s.id}
                      onClick={() => onSelectStudent(s)}
                      className={`vcis-table-row ${isSelected ? "is-selected" : ""}`}
                      style={{
                        cursor: "pointer",
                        backgroundColor: isSelected ? "rgba(59, 130, 246, 0.12)" : undefined,
                      }}
                    >
                      <td style={{ fontWeight: "var(--vcis-font-weight-semibold)", color: "var(--vcis-text)" }}>
                        {s.roll_number}
                      </td>
                      <td style={{ color: "var(--vcis-text)" }}>
                        {s.name}
                      </td>
                      <td style={{ color: "var(--vcis-text-muted)", fontSize: "var(--vcis-font-size-xs)" }}>
                        {deptMap.get(s.department_id) || `Dept #${s.department_id}`}
                      </td>
                      <td style={{ color: "var(--vcis-text-secondary)" }}>
                        Sem {s.current_semester}
                      </td>
                      <td>
                        {intervCount > 0 ? (
                          <span className="vcis-status vcis-status-danger" style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem" }}>
                            {intervCount} Action{intervCount > 1 ? "s" : ""}
                          </span>
                        ) : (
                          <span style={{ color: "var(--vcis-text-muted)", fontSize: "var(--vcis-font-size-xs)" }}>
                            None
                          </span>
                        )}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectStudent(s);
                          }}
                          className={`vcis-btn vcis-btn-sm ${isSelected ? "vcis-btn-primary" : "vcis-btn-secondary"}`}
                          style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
                        >
                          {isSelected ? "Reviewing" : "Review"}
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
