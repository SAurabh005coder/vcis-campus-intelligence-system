import React, { useState } from "react";
import type {
  CreateInterventionRequest,
  InterventionType,
} from "../../api/facultyApi";
import type { StudentProfile } from "../../api/studentApi";
import type { PredictionResponse } from "../../api/predictionApi";

interface InterventionFormProps {
  student: StudentProfile;
  facultyId: number;
  prediction: PredictionResponse;
  onSubmit: (payload: CreateInterventionRequest) => Promise<void>;
  onClose: () => void;
  isSubmitting: boolean;
}

export const InterventionForm: React.FC<InterventionFormProps> = ({
  student,
  facultyId,
  prediction,
  onSubmit,
  onClose,
  isSubmitting,
}) => {
  const [interventionType, setInterventionType] = useState<InterventionType>("extra_class");
  const [actionPlan, setActionPlan] = useState("");
  const [description, setDescription] = useState("");
  const [followUpDate, setFollowUpDate] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!actionPlan.trim()) {
      setFormError("Please provide an action plan for the intervention.");
      return;
    }

    try {
      await onSubmit({
        student_id: student.id,
        faculty_id: facultyId,
        semester: student.current_semester,
        intervention_type: interventionType,
        trigger_predicted_score: prediction.predicted_final_semester_score,
        trigger_academic_status: prediction.academic_status,
        action_plan: actionPlan.trim(),
        description: description.trim() || null,
        follow_up_date: followUpDate ? followUpDate : null,
      });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message);
      } else {
        setFormError("Failed to assign intervention.");
      }
    }
  };

  return (
    <div className="vcis-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="intervention-modal-title">
      <div className="vcis-modal">
        {/* Header */}
        <div className="vcis-modal-header">
          <div>
            <h3 id="intervention-modal-title" className="vcis-modal-title">
              Assign Academic Intervention
            </h3>
            <p className="vcis-modal-subtitle">
              Student: <strong style={{ color: "var(--vcis-text)" }}>{student.name}</strong> ({student.roll_number}) • Sem {student.current_semester}
            </p>
          </div>
          <button
            type="button"
            className="vcis-modal-close-btn"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close dialog"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="vcis-modal-body" style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
            {formError && (
              <div className="vcis-error" role="alert">
                {formError}
              </div>
            )}

            {/* Academic Trigger Banner */}
            <div
              style={{
                backgroundColor: "var(--vcis-surface-raised)",
                border: "1px solid var(--vcis-border)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-3) var(--space-4)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "var(--space-2)",
              }}
            >
              <div>
                <span className="vcis-kpi-label">Trigger Status</span>
                <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginTop: "0.15rem" }}>
                  <span
                    className={`vcis-status ${
                      prediction.academic_status === "INTERVENTION"
                        ? "vcis-status-danger"
                        : prediction.academic_status === "MONITOR"
                        ? "vcis-status-warning"
                        : "vcis-status-success"
                    }`}
                  >
                    {prediction.academic_status}
                  </span>
                  <span style={{ fontSize: "var(--font-xs)", color: "var(--vcis-text-secondary)" }}>
                    Predicted Score: <strong style={{ color: "var(--vcis-text)" }}>{prediction.predicted_final_semester_score.toFixed(1)}%</strong>
                  </span>
                </div>
              </div>
            </div>

            {/* Intervention Type */}
            <div>
              <label htmlFor="intervention-type" className="vcis-label">
                Intervention Strategy <span style={{ color: "var(--vcis-danger)" }}>*</span>
              </label>
              <select
                id="intervention-type"
                value={interventionType}
                onChange={(e) => setInterventionType(e.target.value as InterventionType)}
                className="vcis-select"
                disabled={isSubmitting}
                required
              >
                <option value="extra_class">Extra / Remedial Class</option>
                <option value="additional_assignment">Additional Coursework / Assignment</option>
                <option value="counselling">One-on-One Academic Counselling</option>
                <option value="monitoring">Close Performance Monitoring</option>
              </select>
            </div>

            {/* Action Plan */}
            <div>
              <label htmlFor="intervention-action-plan" className="vcis-label">
                Action Plan & Objectives <span style={{ color: "var(--vcis-danger)" }}>*</span>
              </label>
              <textarea
                id="intervention-action-plan"
                value={actionPlan}
                onChange={(e) => setActionPlan(e.target.value)}
                rows={3}
                placeholder="Specific guidance, remedial sessions, topic revision, or coursework target..."
                className="vcis-input"
                style={{ width: "100%", resize: "vertical" }}
                disabled={isSubmitting}
                required
              />
            </div>

            {/* Description / Background */}
            <div>
              <label htmlFor="intervention-description" className="vcis-label">
                Context / Initial Observations (Optional)
              </label>
              <textarea
                id="intervention-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                placeholder="Observed learning gaps, weak milestones, or faculty notes..."
                className="vcis-input"
                style={{ width: "100%", resize: "vertical" }}
                disabled={isSubmitting}
              />
            </div>

            {/* Follow-up Date */}
            <div>
              <label htmlFor="intervention-follow-up-date" className="vcis-label">
                Scheduled Follow-up Date (Optional)
              </label>
              <input
                type="date"
                id="intervention-follow-up-date"
                value={followUpDate}
                onChange={(e) => setFollowUpDate(e.target.value)}
                className="vcis-input"
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Footer */}
          <div className="vcis-modal-footer">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="vcis-button vcis-button-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              id="submit-intervention-btn"
              disabled={isSubmitting}
              className="vcis-button vcis-button-primary"
            >
              {isSubmitting ? "Assigning..." : "Assign Intervention"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InterventionForm;
