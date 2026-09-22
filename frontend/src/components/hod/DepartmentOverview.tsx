import React from "react";
import type { StudentProfile, CourseInfo } from "../../api/studentApi";

interface DepartmentOverviewProps {
  students: StudentProfile[];
  courses: CourseInfo[];
  departmentId: number;
}

export const DepartmentOverview: React.FC<DepartmentOverviewProps> = ({
  students,
  courses,
  departmentId,
}) => {
  // Filter courses based on department scope
  const scopedCourses = courses.filter((c) => c.department_id === departmentId);

  // Compute semester distribution reliably from department student records
  const sem1Count = students.filter((s) => s.current_semester === 1).length;
  const sem2Count = students.filter((s) => s.current_semester === 2).length;
  const sem3Count = students.filter((s) => s.current_semester === 3).length;
  const sem4Count = students.filter((s) => s.current_semester === 4).length;

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)" }}>
      <div className="vcis-card-header">
        <div>
          <h3 className="vcis-card-title">Department Student Roster & Semester Distribution</h3>
          <p className="vcis-card-subtitle">
            Departmental student cohort distribution and curriculum course scope
          </p>
        </div>
        <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
          Active Courses:{" "}
          <strong style={{ color: "var(--vcis-text)" }}>
            {scopedCourses.map((c) => c.code).join(", ") || "None"}
          </strong>
        </span>
      </div>

      <div className="vcis-card-body">
        <div className="vcis-kpi-grid">
          {/* Total Enrolled */}
          <div className="vcis-kpi-card">
            <div>
              <div className="vcis-kpi-value">
                {students.length}
              </div>
              <div className="vcis-kpi-label">Total Department Students</div>
            </div>
            <div className="vcis-kpi-context">Enrolled cohort</div>
          </div>

          {/* Semester 1 */}
          <div className="vcis-kpi-card">
            <div>
              <div className="vcis-kpi-value">
                {sem1Count}
              </div>
              <div className="vcis-kpi-label">Semester 1</div>
            </div>
            <div className="vcis-kpi-context">Model 1 early phase</div>
          </div>

          {/* Semester 2 */}
          <div className="vcis-kpi-card">
            <div>
              <div className="vcis-kpi-value">
                {sem2Count}
              </div>
              <div className="vcis-kpi-label">Semester 2</div>
            </div>
            <div className="vcis-kpi-context">Model 2 sequential</div>
          </div>

          {/* Semester 3 */}
          <div className="vcis-kpi-card">
            <div>
              <div className="vcis-kpi-value">
                {sem3Count}
              </div>
              <div className="vcis-kpi-label">Semester 3</div>
            </div>
            <div className="vcis-kpi-context">Model 2 sequential</div>
          </div>

          {/* Semester 4 */}
          <div className="vcis-kpi-card">
            <div>
              <div className="vcis-kpi-value">
                {sem4Count}
              </div>
              <div className="vcis-kpi-label">Semester 4</div>
            </div>
            <div className="vcis-kpi-context">Final semester</div>
          </div>
        </div>
      </div>
    </div>
  );
};
