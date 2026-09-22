import React, { useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getRoleHomePath } from "../auth/ProtectedRoute";

interface RoleConfig {
  badgeLabel: string;
  badgeClass: string;
  navItems: Array<{
    label: string;
    path: string;
  }>;
}

const ROLE_CONFIGS: Record<string, RoleConfig> = {
  student: {
    badgeLabel: "Student",
    badgeClass: "vcis-shell-role-student",
    navItems: [
      { label: "Academic Portal", path: "/student" },
    ],
  },
  faculty: {
    badgeLabel: "Faculty",
    badgeClass: "vcis-shell-role-faculty",
    navItems: [
      { label: "Faculty Portal", path: "/faculty" },
    ],
  },
  hod: {
    badgeLabel: "HOD",
    badgeClass: "vcis-shell-role-hod",
    navItems: [
      { label: "Department Oversight", path: "/hod" },
    ],
  },
  admin: {
    badgeLabel: "Administrator",
    badgeClass: "vcis-shell-role-admin",
    navItems: [
      { label: "System Administration", path: "/admin" },
    ],
  },
};

export const AppLayout: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const role = user?.role?.toLowerCase() || "";
  const config: RoleConfig = ROLE_CONFIGS[role] || {
    badgeLabel: user?.role?.toUpperCase() || "Authenticated",
    badgeClass: "vcis-shell-role-student",
    navItems: [],
  };

  const homePath = user?.role ? getRoleHomePath(user.role) : "/login";

  return (
    <div className="vcis-shell">
      {/* Top / Primary Institutional Header */}
      <header className="vcis-shell-topbar" role="banner">
        {/* Left: Brand Identity */}
        <div className="vcis-shell-brand-group">
          <Link to={homePath} className="vcis-shell-brand" aria-label="VCIS Home">
            <div className="vcis-shell-logo-badge" aria-hidden="true">
              <span className="vcis-shell-logo-text">V</span>
            </div>
            <div className="vcis-shell-brand-text">
              <div className="vcis-shell-brand-heading">
                <span className="vcis-shell-title">VCIS</span>
                <span className="vcis-shell-subtitle">Virtual Campus Intelligence System</span>
              </div>
              <span className="vcis-shell-tagline">AI-Powered Academic Intelligence</span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          {config.navItems.length > 0 && (
            <nav className="vcis-shell-nav" aria-label="Role Navigation">
              {config.navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={`vcis-shell-nav-link ${isActive ? "is-active" : ""}`}
                  >
                    {item.label}
                  </NavLink>
                );
              })}
            </nav>
          )}
        </div>

        {/* Center / Right: Role Indicator & User Identity */}
        <div className="vcis-shell-actions">
          {/* Semantic Role Badge */}
          <span
            className={`vcis-shell-role-badge ${config.badgeClass}`}
            role="status"
            aria-label={`Role: ${config.badgeLabel}`}
          >
            {config.badgeLabel}
          </span>

          {/* User Identity */}
          {user && (
            <div className="vcis-shell-user" title={`Logged in as ${user.email}`}>
              <span className="vcis-shell-user-dot" aria-hidden="true" />
              <span className="vcis-shell-user-email">{user.email}</span>
            </div>
          )}

          {/* Logout Action */}
          <button
            type="button"
            onClick={logout}
            className="vcis-shell-logout-btn"
            aria-label="Sign out of VCIS"
          >
            Sign Out
          </button>

          {/* Mobile Menu Toggle */}
          <button
            type="button"
            className="vcis-shell-mobile-btn"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={mobileMenuOpen}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              {mobileMenuOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </>
              ) : (
                <>
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </>
              )}
            </svg>
          </button>
        </div>
      </header>

      {/* Mobile Collapsible Navigation Drawer */}
      {mobileMenuOpen && (
        <div
          className={`vcis-shell-mobile-menu ${mobileMenuOpen ? "is-open" : ""}`}
          role="navigation"
          aria-label="Mobile Navigation"
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className={`vcis-shell-role-badge ${config.badgeClass}`}>
              {config.badgeLabel}
            </span>
            {user && (
              <span style={{ fontSize: "0.82rem", color: "var(--vcis-text-secondary)" }}>
                {user.email}
              </span>
            )}
          </div>

          {config.navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`vcis-shell-nav-link ${isActive ? "is-active" : ""}`}
                style={{ width: "100%", justifyContent: "flex-start", padding: "0.6rem 0.8rem" }}
              >
                {item.label}
              </NavLink>
            );
          })}

          <button
            type="button"
            onClick={() => {
              setMobileMenuOpen(false);
              logout();
            }}
            className="vcis-button vcis-button-danger vcis-button-sm"
            style={{ width: "100%", marginTop: "var(--space-2)" }}
          >
            Sign Out
          </button>
        </div>
      )}

      {/* Main Authenticated Content Container */}
      <main className="vcis-shell-main" role="main">
        {children || <Outlet />}
      </main>
    </div>
  );
};

export default AppLayout;