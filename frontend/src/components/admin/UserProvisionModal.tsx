import React, { useState } from "react";
import type { CreateUserRequest, UserRole } from "../../api/adminApi";

interface UserProvisionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: CreateUserRequest) => Promise<void>;
  isSubmitting: boolean;
}

export const UserProvisionModal: React.FC<UserProvisionModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
}) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("student");
  const [formError, setFormError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!email.trim() || !password.trim()) {
      setFormError("Email and password are required.");
      return;
    }

    if (password.length < 6) {
      setFormError("Password must be at least 6 characters.");
      return;
    }

    try {
      await onSubmit({
        email: email.trim().toLowerCase(),
        password,
        role,
      });
      setEmail("");
      setPassword("");
      setRole("student");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message);
      } else {
        setFormError("Failed to provision user.");
      }
    }
  };

  return (
    <div className="vcis-modal-backdrop" role="dialog" aria-modal="true">
      <div className="vcis-modal" style={{ maxWidth: "520px" }}>
        {/* Modal Header */}
        <div className="vcis-modal-header">
          <div>
            <h3 className="vcis-modal-title">
              Provision System User Account
            </h3>
            <p className="vcis-modal-subtitle">
              Registers authentication identity in PostgreSQL users store
            </p>
          </div>
          <button
            id="close-provision-modal-btn"
            onClick={onClose}
            className="vcis-modal-close-btn"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit}>
          <div className="vcis-modal-body">
            {formError && (
              <div className="vcis-alert vcis-alert-danger" style={{ marginBottom: "var(--space-4)" }}>
                ✕ {formError}
              </div>
            )}

            {/* Email */}
            <div className="vcis-form-group">
              <label htmlFor="user_email" className="vcis-form-label">
                Email Address *
              </label>
              <input
                id="user_email"
                type="email"
                required
                placeholder="e.g., scholar@institution.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="vcis-input"
              />
            </div>

            {/* Password */}
            <div className="vcis-form-group">
              <label htmlFor="user_password" className="vcis-form-label">
                Initial Password *
              </label>
              <input
                id="user_password"
                type="password"
                required
                placeholder="Minimum 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="vcis-input"
              />
            </div>

            {/* System Role */}
            <div className="vcis-form-group">
              <label htmlFor="user_role" className="vcis-form-label">
                System Role *
              </label>
              <select
                id="user_role"
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="vcis-select"
              >
                <option value="student">Student (Role: student)</option>
                <option value="faculty">Faculty (Role: faculty)</option>
                <option value="hod">Head of Department (Role: hod)</option>
                <option value="admin">System Administrator (Role: admin)</option>
              </select>
            </div>

            <div
              style={{
                padding: "var(--space-3) var(--space-4)",
                backgroundColor: "var(--vcis-surface-soft)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--vcis-border)",
                fontSize: "var(--vcis-font-size-xs)",
                color: "var(--vcis-text-secondary)",
                lineHeight: 1.5,
              }}
            >
              ℹ️ The system provisions the account with a cryptographically hashed password. Domain workflows will bind to student or faculty records referencing this identifier.
            </div>
          </div>

          {/* Modal Footer */}
          <div className="vcis-modal-footer">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="vcis-btn vcis-btn-secondary"
            >
              Cancel
            </button>
            <button
              id="submit-provision-user-btn"
              type="submit"
              disabled={isSubmitting}
              className="vcis-btn vcis-btn-primary"
            >
              {isSubmitting ? "Provisioning..." : "Provision Account"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserProvisionModal;
