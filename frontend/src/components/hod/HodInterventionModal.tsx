import React, { useState } from "react";
import type {
  CreateInterventionRequest,
  InterventionType,
  FacultyProfile,
} from "../../api/facultyApi";
import type { StudentProfile } from "../../api/studentApi";
import type { PredictionResponse } from "../../api/predictionApi";

interface HodInterventionModalProps {
  student: StudentProfile;
  defaultFacultyId: number | null;
  facultyList: FacultyProfile[];
  prediction: PredictionResponse;
  onSubmit: (payload: CreateInterventionRequest) => Promise<void>;
  onClose: () => void;
  isSubmitting: boolean;
}

export const HodInterventionModal: React.FC<HodInterventionModalProps> = ({
  student,
  defaultFacultyId,
  facultyList,
  prediction,
  onSubmit,
  onClose,
  isSubmitting,
}) => {
  const [selectedFacultyId, setSelectedFacultyId] = useState<number>(
    defaultFacultyId || (facultyList.length > 0 ? facultyList[0].id : 1)
  );
  const [interventionType, setInterventionType] =
    useState<InterventionType>("extra_class");
  const [actionPlan, setActionPlan] = useState("");
  const [description, setDescription] = useState("");
  const [followUpDate, setFollowUpDate] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!selectedFacultyId) {
      setFormError("Please select a supervising faculty member.");
      return;
    }

    if (!actionPlan.trim()) {
      setFormError("Please provide a remedial action plan.");
      return;
    }

    try {
      await onSubmit({
        student_id: student.id,
        faculty_id: selectedFacultyId,
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
    <div className="vcis-modal-backdrop" onClick={onClose}>
      <div
        className="vcis-modal"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="vcis-modal-header">
          <div>
            <h3 className="vcis-modal-title">HOD Academic Intervention Assignment</h3>
            <p className="vcis-modal-subtitle">
              Student: {student.name} ({student.roll_number}) • Semester {student.current_semester}
            </p>
          </div>
          <button
            type="button"
            className="vcis-modal-close-btn"
            onClick={onClose}
            aria-label="Close dialog"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit}>
          <div className="vcis-modal-body">
            {formError && (
              <div className="vcis-alert vcis-alert-danger" style={{ marginBottom: "var(--space-4)" }}>
                {formError}
              </div>
            )}

            {/* Immutable Trigger Evidence */}
            <div
              style={{
                padding: "var(--space-3) var(--space-4)",
                backgroundColor: "var(--vcis-surface-muted)",
                borderRadius: "var(--radius-md)",
                borderLeft: "4px solid var(--vcis-accent)",
                marginBottom: "var(--space-4)",
                fontSize: "var(--vcis-font-size-xs)",
                color: "var(--vcis-text-secondary)",
              }}
            >
              <strong>Trigger Evidence (Immutable):</strong> Predicted Score:{" "}
              <strong style={{ color: "var(--vcis-text)" }}>{prediction.predicted_final_semester_score.toFixed(2)}%</strong> •
              Academic Status: <strong style={{ color: "var(--vcis-text)" }}>{prediction.academic_status}</strong>
            </div>

            {/* Supervising / Managing Faculty */}
            <div className="vcis-form-group">
              <label htmlFor="hod_faculty_id" className="vcis-form-label">
                Supervising Faculty Member *
              </label>
              <select
                id="hod_faculty_id"
                value={selectedFacultyId}
                onChange={(e) => setSelectedFacultyId(Number(e.target.value))}
                className="vcis-form-select"
              >
                {facultyList.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.first_name} {f.last_name} ({f.employee_code}) — {f.designation}
                  </option>
                ))}
              </select>
            </div>

            {/* Intervention Type */}
            <div className="vcis-form-group">
              <label htmlFor="hod_intervention_type" className="vcis-form-label">
                Intervention Type *
              </label>
              <select
                id="hod_intervention_type"
                value={interventionType}
                onChange={(e) =>
                  setInterventionType(e.target.value as InterventionType)
                }
                className="vcis-form-select"
              >
                <option value="extra_class">Extra / Remedial Class</option>
                <option value="additional_assignment">Additional Assignment</option>
                <option value="counselling">Academic Counselling</option>
                <option value="monitoring">Performance Monitoring</option>
              </select>
            </div>

            {/* Action Plan */}
            <div className="vcis-form-group">
              <label htmlFor="hod_action_plan" className="vcis-form-label">
                Action Plan *
              </label>
              <textarea
                id="hod_action_plan"
                required
                rows={3}
                placeholder="Detail the remedial steps, timetable, and milestones required for the student..."
                value={actionPlan}
                onChange={(e) => setActionPlan(e.target.value)}
                className="vcis-form-textarea"
              />
            </div>

            {/* Context Notes */}
            <div className="vcis-form-group">
              <label htmlFor="hod_description" className="vcis-form-label">
                Contextual Notes (Optional)
              </label>
              <textarea
                id="hod_description"
                rows={2}
                placeholder="Specific notes or departmental observations..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="vcis-form-textarea"
              />
            </div>

            {/* Follow-up Date */}
            <div className="vcis-form-group" style={{ marginBottom: 0 }}>
              <label htmlFor="hod_follow_up_date" className="vcis-form-label">
                Follow-Up Review Date (Optional)
              </label>
              <input
                id="hod_follow_up_date"
                type="date"
                value={followUpDate}
                onChange={(e) => setFollowUpDate(e.target.value)}
                className="vcis-form-input"
              />
            </div>
          </div>

          {/* Footer Actions */}
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
              type="submit"
              disabled={isSubmitting}
              className="vcis-btn vcis-btn-primary"
            >
              {isSubmitting ? "Persisting..." : "Confirm & Assign"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
