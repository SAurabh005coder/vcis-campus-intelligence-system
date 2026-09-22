import React from "react";
import type { AdminProfile } from "../../api/adminApi";

interface AdminOverviewProps {
  admin: AdminProfile | null;
  totalUsers: number;
  totalStudents: number;
  totalFaculty: number;
  totalDepartments: number;
  totalCourses: number;
  totalSubjects: number;
  totalInterventions: number;
  onOpenProvisionModal: () => void;
}

export const AdminOverview: React.FC<AdminOverviewProps> = ({
  admin,
  totalUsers,
  totalStudents,
  totalFaculty,
  totalDepartments,
  totalCourses,
  totalSubjects,
  totalInterventions,
  onOpenProvisionModal,
}) => {
  return (
    <div style={{ marginBottom: "var(--space-6)" }}>
      {/* Welcome & Institutional Identity Card */}
      <div className="vcis-welcome-card" style={{ marginBottom: "var(--space-5)" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
            <h2 className="vcis-welcome-title">
              Institutional Administration
            </h2>
            <span className="vcis-role-badge-admin" style={{ padding: "0.15rem 0.5rem", borderRadius: "var(--radius-pill)", fontSize: "var(--vcis-font-size-xs)", fontWeight: 700, letterSpacing: "0.05em" }}>
              ADMIN
            </span>
          </div>
          <p className="vcis-welcome-subtitle">
            {admin?.email || "admin@institution.edu"} • {admin?.designation || "System Administrator"} • Institutional Scope
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap" }}>
          <div className="vcis-meta-pill-group">
            <div className="vcis-meta-pill">
              <span className="vcis-meta-label">System Scope:</span>
              <span className="vcis-meta-value">All Departments</span>
            </div>
            <div className="vcis-meta-pill">
              <span className="vcis-meta-label">Security Tier:</span>
              <span className="vcis-meta-value" style={{ color: "var(--vcis-primary)" }}>Level 1 Admin</span>
            </div>
          </div>

          <button
            id="admin-provision-user-btn"
            onClick={onOpenProvisionModal}
            className="vcis-btn vcis-btn-primary"
          >
            + Provision User
          </button>
        </div>
      </div>

      {/* Primary Institutional Counts */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
          gap: "var(--space-4)",
          marginBottom: "var(--space-4)",
        }}
      >
        <div className="vcis-kpi-card" style={{ borderTop: "3px solid var(--vcis-primary)" }}>
          <div>
            <div className="vcis-kpi-value" style={{ color: "var(--vcis-primary)" }}>
              {totalStudents}
            </div>
            <div className="vcis-kpi-label">Enrolled Students</div>
          </div>
          <div className="vcis-kpi-context">Registered across all departments</div>
        </div>

        <div className="vcis-kpi-card" style={{ borderTop: "3px solid var(--vcis-success)" }}>
          <div>
            <div className="vcis-kpi-value" style={{ color: "var(--vcis-success)" }}>
              {totalFaculty}
            </div>
            <div className="vcis-kpi-label">Faculty Members</div>
          </div>
          <div className="vcis-kpi-context">Instructors & department heads</div>
        </div>

        <div className="vcis-kpi-card" style={{ borderTop: "3px solid var(--vcis-accent)" }}>
          <div>
            <div className="vcis-kpi-value" style={{ color: "var(--vcis-accent)" }}>
              {totalUsers}
            </div>
            <div className="vcis-kpi-label">User Accounts</div>
          </div>
          <div className="vcis-kpi-context">Total authentication identities</div>
        </div>
      </div>

      {/* Secondary Operational Entities */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
          gap: "var(--space-4)",
        }}
      >
        <div className="vcis-kpi-card">
          <div>
            <div className="vcis-kpi-value" style={{ fontSize: "1.45rem", color: "var(--vcis-text)" }}>
              {totalDepartments}
            </div>
            <div className="vcis-kpi-label">Departments</div>
          </div>
          <div className="vcis-kpi-context">Academic faculties</div>
        </div>

        <div className="vcis-kpi-card">
          <div>
            <div className="vcis-kpi-value" style={{ fontSize: "1.45rem", color: "var(--vcis-text)" }}>
              {totalCourses}
            </div>
            <div className="vcis-kpi-label">Degree Courses</div>
          </div>
          <div className="vcis-kpi-context">Active degree programs</div>
        </div>

        <div className="vcis-kpi-card">
          <div>
            <div className="vcis-kpi-value" style={{ fontSize: "1.45rem", color: "var(--vcis-text)" }}>
              {totalSubjects}
            </div>
            <div className="vcis-kpi-label">Curriculum Subjects</div>
          </div>
          <div className="vcis-kpi-context">Coursework modules</div>
        </div>

        <div className="vcis-kpi-card">
          <div>
            <div className="vcis-kpi-value" style={{ fontSize: "1.45rem", color: "var(--vcis-warning)" }}>
              {totalInterventions}
            </div>
            <div className="vcis-kpi-label">Active Interventions</div>
          </div>
          <div className="vcis-kpi-context">System remedial workflows</div>
        </div>
      </div>
    </div>
  );
};

export default AdminOverview;
