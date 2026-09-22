import React from "react";
import { useAuth } from "../../auth/AuthContext";

interface RoleLandingProps {
  roleTitle: string;
  roleBadge: string;
  badgeColor: string;
  description: string;
}

export const RoleLandingLayout: React.FC<RoleLandingProps> = ({
  roleTitle,
  roleBadge,
  badgeColor,
  description,
}) => {
  const { user, logout } = useAuth();

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#f7fafc",
        fontFamily: "system-ui, -apple-system, sans-serif",
        color: "#2d3748",
      }}
    >
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "1rem 2rem",
          backgroundColor: "#ffffff",
          borderBottom: "1px solid #e2e8f0",
          boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <h2 style={{ margin: 0, fontSize: "1.25rem", color: "#1a202c" }}>
            VCIS 3.0
          </h2>
          <span
            style={{
              padding: "0.25rem 0.6rem",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              backgroundColor: badgeColor,
              color: "#ffffff",
            }}
          >
            {roleBadge}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
          <span style={{ fontSize: "0.9rem", color: "#4a5568" }}>
            {user?.email}
          </span>
          <button
            onClick={logout}
            style={{
              padding: "0.4rem 0.9rem",
              borderRadius: "6px",
              border: "1px solid #cbd5e0",
              backgroundColor: "#ffffff",
              color: "#4a5568",
              cursor: "pointer",
              fontSize: "0.85rem",
              fontWeight: 500,
              transition: "all 0.2s",
            }}
          >
            Sign Out
          </button>
        </div>
      </header>

      <main style={{ maxWidth: "1000px", margin: "2rem auto", padding: "0 1.5rem" }}>
        <div
          style={{
            backgroundColor: "#ffffff",
            borderRadius: "8px",
            border: "1px solid #e2e8f0",
            padding: "2rem",
            boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
          }}
        >
          <h1 style={{ marginTop: 0, fontSize: "1.75rem", color: "#1a202c" }}>
            {roleTitle}
          </h1>
          <p style={{ fontSize: "1rem", color: "#718096", lineHeight: 1.6 }}>
            {description}
          </p>

          <div
            style={{
              marginTop: "2rem",
              padding: "1rem",
              borderRadius: "6px",
              backgroundColor: "#edf2f7",
              borderLeft: `4px solid ${badgeColor}`,
            }}
          >
            <p style={{ margin: 0, fontSize: "0.9rem", color: "#4a5568" }}>
              <strong>Authentication Verified:</strong> You are securely
              authenticated with role <code>{user?.role}</code>. Detailed
              subsystem views (dashboard metrics, predictions, interventions) will
              be integrated in subsequent development phases.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};
