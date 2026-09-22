import React, { useMemo, useState } from "react";
import type { UserResponse, UserRole } from "../../api/adminApi";

interface AdminUserDirectoryProps {
  users: UserResponse[];
  isLoading: boolean;
  onOpenProvisionModal: () => void;
}

export const AdminUserDirectory: React.FC<AdminUserDirectoryProps> = ({
  users,
  isLoading,
  onOpenProvisionModal,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const filteredUsers = useMemo(() => {
    return users.filter((u) => {
      const matchesSearch = u.email.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesRole = roleFilter === "all" || u.role.toLowerCase() === roleFilter.toLowerCase();
      const matchesStatus =
        statusFilter === "all"
          ? true
          : statusFilter === "active"
          ? u.is_active
          : !u.is_active;

      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, searchTerm, roleFilter, statusFilter]);

  const getRoleBadgeClass = (role: UserRole) => {
    switch (role.toLowerCase()) {
      case "admin":
        return "vcis-role-badge-admin";
      case "hod":
        return "vcis-role-badge-hod";
      case "faculty":
        return "vcis-role-badge-faculty";
      case "student":
        return "vcis-role-badge-student";
      default:
        return "vcis-badge-neutral";
    }
  };

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)" }}>
      {/* Header */}
      <div className="vcis-card-header">
        <div>
          <h3 style={{ margin: 0, fontSize: "var(--vcis-font-size-md)", fontWeight: "var(--vcis-font-weight-semibold)", color: "var(--vcis-text)" }}>
            Institutional User Accounts Register
          </h3>
          <p style={{ margin: "var(--space-1) 0 0 0", fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
            Authentication identities across all institutional roles
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
          <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
            Showing {filteredUsers.length} of {users.length} accounts
          </span>
          <button
            id="user-directory-provision-btn"
            onClick={onOpenProvisionModal}
            className="vcis-btn vcis-btn-primary vcis-btn-sm"
          >
            + Provision User
          </button>
        </div>
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
              id="admin-user-search-input"
              type="text"
              placeholder="Search by email identifier..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="vcis-input"
            />
          </div>

          <div style={{ width: "160px" }}>
            <select
              id="admin-user-role-filter"
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="vcis-select"
            >
              <option value="all">All Roles</option>
              <option value="student">Student</option>
              <option value="faculty">Faculty</option>
              <option value="hod">HOD</option>
              <option value="admin">Administrator</option>
            </select>
          </div>

          <div style={{ width: "160px" }}>
            <select
              id="admin-user-status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="vcis-select"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active Accounts</option>
              <option value="inactive">Inactive Accounts</option>
            </select>
          </div>
        </div>

        {/* Users Table */}
        {isLoading ? (
          <div style={{ padding: "var(--space-8)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
            Loading user identities...
          </div>
        ) : filteredUsers.length === 0 ? (
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
            No user accounts found matching the filter criteria.
          </div>
        ) : (
          <div className="vcis-table-wrapper" style={{ maxHeight: "420px" }}>
            <table className="vcis-table">
              <thead className="vcis-table-header">
                <tr>
                  <th style={{ width: "100px" }}>User ID</th>
                  <th>Email / Identity</th>
                  <th style={{ width: "160px" }}>System Role</th>
                  <th style={{ width: "120px", textAlign: "right" }}>Account Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((u) => {
                  const roleClass = getRoleBadgeClass(u.role);
                  return (
                    <tr key={u.id} className="vcis-table-row">
                      <td className="vcis-table-cell" style={{ fontWeight: 600, color: "var(--vcis-text-muted)" }}>
                        #{u.id}
                      </td>
                      <td className="vcis-table-cell" style={{ fontWeight: 500, color: "var(--vcis-text)" }}>
                        {u.email}
                      </td>
                      <td className="vcis-table-cell">
                        <span
                          className={roleClass}
                          style={{
                            padding: "0.15rem 0.55rem",
                            borderRadius: "var(--radius-pill)",
                            fontSize: "0.72rem",
                            fontWeight: 700,
                            letterSpacing: "0.04em",
                            textTransform: "uppercase",
                            display: "inline-block",
                          }}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td className="vcis-table-cell" style={{ textAlign: "right" }}>
                        <span
                          className={`vcis-badge ${u.is_active ? "vcis-badge-success" : "vcis-badge-danger"}`}
                        >
                          {u.is_active ? "Active" : "Inactive"}
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

export default AdminUserDirectory;
