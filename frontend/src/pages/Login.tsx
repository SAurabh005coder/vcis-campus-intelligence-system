import React, { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getRoleHomePath } from "../auth/ProtectedRoute";

export const Login: React.FC = () => {
  const { isAuthenticated, user, login, isLoading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // If already authenticated and not loading, redirect to role home
  if (!isLoading && isAuthenticated && user) {
    return <Navigate to={getRoleHomePath(user.role)} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email.trim() || !password) {
      setErrorMessage("Please enter both email and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const loggedInUser = await login({ email: email.trim(), password });
      navigate(getRoleHomePath(loggedInUser.role), { replace: true });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected error occurred during login. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "var(--vcis-bg, #f8fafc)",
        fontFamily: "var(--vcis-font-sans, system-ui, sans-serif)",
        padding: "1.5rem",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "420px",
          backgroundColor: "var(--vcis-surface, #ffffff)",
          borderRadius: "var(--radius-lg, 10px)",
          boxShadow: "var(--shadow-card, 0 1px 3px rgba(0, 0, 0, 0.05))",
          border: "1px solid var(--vcis-border, #e2e8f0)",
          overflow: "hidden",
        }}
      >
        {/* Header Header/Branding */}
        <div
          style={{
            backgroundColor: "#0f172a",
            padding: "2rem 1.5rem",
            textAlign: "center",
            color: "#ffffff",
          }}
        >
          <h1 style={{ margin: 0, fontSize: "1.6rem", fontWeight: 700, letterSpacing: "-0.02em" }}>
            VCIS
          </h1>
          <p style={{ margin: "0.4rem 0 0 0", fontSize: "0.875rem", color: "#cbd5e1" }}>
            Virtual Campus Intelligence System
          </p>
          <p style={{ margin: "0.3rem 0 0 0", fontSize: "0.72rem", color: "#38bdf8", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600 }}>
            AI-Powered Academic Intelligence
          </p>
        </div>

        {/* Form Body */}
        <div style={{ padding: "2rem" }}>
          <h2
            style={{
              margin: "0 0 1.5rem 0",
              fontSize: "1.25rem",
              fontWeight: 600,
              color: "var(--vcis-text, #0f172a)",
            }}
          >
            Sign In to Portal
          </h2>

          {errorMessage && (
            <div
              role="alert"
              style={{
                marginBottom: "1.25rem",
                padding: "0.75rem 1rem",
                backgroundColor: "var(--vcis-danger-soft, #fef2f2)",
                border: "1px solid var(--vcis-danger-border, #fecaca)",
                borderRadius: "var(--radius-md, 6px)",
                color: "var(--vcis-danger-text, #991b1b)",
                fontSize: "0.875rem",
                lineHeight: 1.4,
              }}
            >
              {errorMessage}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: "1.25rem" }}>
              <label
                htmlFor="email"
                style={{
                  display: "block",
                  marginBottom: "0.5rem",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: "var(--vcis-text-secondary, #475569)",
                }}
              >
                Institutional Email
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                placeholder="name@institution.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isSubmitting}
                className="vcis-input"
              />
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <label
                htmlFor="password"
                style={{
                  display: "block",
                  marginBottom: "0.5rem",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: "var(--vcis-text-secondary, #475569)",
                }}
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isSubmitting}
                className="vcis-input"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="vcis-button vcis-button-primary"
              style={{
                width: "100%",
                height: "40px",
                fontSize: "0.9375rem",
                fontWeight: 600,
              }}
            >
              {isSubmitting ? (
                <>
                  <span>Signing In...</span>
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          <div
            style={{
              marginTop: "1.5rem",
              paddingTop: "1.25rem",
              borderTop: "1px solid #e2e8f0",
              textAlign: "center",
              fontSize: "0.8rem",
              color: "#a0aec0",
            }}
          >
            Role-Based Access Control Protected System
          </div>
        </div>
      </div>
    </div>
  );
};
