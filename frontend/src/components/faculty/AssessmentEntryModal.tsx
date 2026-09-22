import React, { useState } from "react";
import type { AllowedAssessmentType, AssessmentCreateRequest } from "../../api/facultyApi";
import type { EnrollmentResultResponse, StudentProfile } from "../../api/studentApi";

interface AssessmentEntryModalProps {
  student: StudentProfile;
  enrollments: EnrollmentResultResponse[];
  onSubmit: (payload: AssessmentCreateRequest) => Promise<void>;
  onClose: () => void;
  isSubmitting: boolean;
}

export const AssessmentEntryModal: React.FC<AssessmentEntryModalProps> = ({
  student,
  enrollments,
  onSubmit,
  onClose,
  isSubmitting,
}) => {
  // Default to the first available enrollment ID if present
  const [selectedEnrollmentId, setSelectedEnrollmentId] = useState<number>(
    enrollments.length > 0 ? enrollments[0].enrollment_id : 0
  );

  // Expose ONLY CT1 and ASSIGNMENT
  const [assessmentType, setAssessmentType] = useState<AllowedAssessmentType>("CT1");
  const [assessmentName, setAssessmentName] = useState<string>("CT1");
  const [maxMarks, setMaxMarks] = useState<number>(20);
  const [obtainedMarks, setObtainedMarks] = useState<number>(16);
  const [assessmentDate, setAssessmentDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [remarks, setRemarks] = useState<string>("");
  const [formError, setFormError] = useState<string | null>(null);

  // When switching assessment type, suggest appropriate default names and marks if untouched
  const handleTypeChange = (newType: AllowedAssessmentType) => {
    setAssessmentType(newType);
    if (newType === "CT1") {
      setAssessmentName("CT1");
      if (maxMarks === 25 || maxMarks === 10) setMaxMarks(20);
    } else {
      setAssessmentName("Assignment 1");
      if (maxMarks === 20) setMaxMarks(25);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!selectedEnrollmentId || selectedEnrollmentId <= 0) {
      setFormError("Please select an enrolled subject to record assessment marks.");
      return;
    }

    const trimmedName = assessmentName.trim();
    if (!trimmedName || trimmedName.length < 2) {
      setFormError("Assessment name must be at least 2 characters long.");
      return;
    }

    if (trimmedName.length > 150) {
      setFormError("Assessment name cannot exceed 150 characters.");
      return;
    }

    if (isNaN(maxMarks) || maxMarks <= 0 || maxMarks > 1000) {
      setFormError("Maximum marks must be a positive integer between 1 and 1000.");
      return;
    }

    if (isNaN(obtainedMarks) || obtainedMarks < 0 || obtainedMarks > 1000) {
      setFormError("Obtained marks must be a non-negative integer between 0 and 1000.");
      return;
    }

    if (obtainedMarks > maxMarks) {
      setFormError(`Obtained marks (${obtainedMarks}) cannot exceed maximum marks (${maxMarks}).`);
      return;
    }

    if (!assessmentDate) {
      setFormError("Please select a valid assessment date.");
      return;
    }

    if (remarks.length > 1000) {
      setFormError("Remarks cannot exceed 1000 characters.");
      return;
    }

    try {
      await onSubmit({
        enrollment_id: selectedEnrollmentId,
        assessment_type: assessmentType,
        assessment_name: trimmedName,
        max_marks: Math.round(maxMarks),
        obtained_marks: Math.round(obtainedMarks),
        assessment_date: assessmentDate,
        remarks: remarks.trim() ? remarks.trim() : null,
      });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message);
      } else {
        setFormError("Failed to record assessment. Please check inputs and try again.");
      }
    }
  };

  return (
    <div className="vcis-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="assessment-modal-title">
      <div className="vcis-modal">
        {/* Header */}
        <div className="vcis-modal-header">
          <div>
            <h3 id="assessment-modal-title" className="vcis-modal-title">
              Record Assessment Marks
            </h3>
            <p className="vcis-modal-subtitle">
              Student: <strong style={{ color: "var(--vcis-text)" }}>{student.name}</strong> ({student.roll_number})
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

            {/* Subject Selector */}
            <div>
              <label htmlFor="assessment-subject" className="vcis-label">
                Enrolled Subject <span style={{ color: "var(--vcis-danger)" }}>*</span>
              </label>
              <select
                id="assessment-subject"
                value={selectedEnrollmentId}
                onChange={(e) => setSelectedEnrollmentId(Number(e.target.value))}
                className="vcis-select"
                disabled={isSubmitting || enrollments.length === 0}
                required
              >
                {enrollments.length === 0 ? (
                  <option value={0}>No enrolled subjects found for this student</option>
                ) : (
                  enrollments.map((enr) => (
                    <option key={enr.enrollment_id} value={enr.enrollment_id}>
                      {enr.subject_name || `Subject #${enr.subject_id}`}
                      {enr.subject_code ? ` (${enr.subject_code})` : ""}
                      {enr.semester ? ` — Sem ${enr.semester}` : ""}
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Assessment Type Toggle */}
            <div>
              <label htmlFor="assessment-type" className="vcis-label">
                Early Assessment Type <span style={{ color: "var(--vcis-danger)" }}>*</span>
              </label>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "var(--space-2)",
                }}
              >
                <button
                  type="button"
                  id="type-ct1"
                  onClick={() => handleTypeChange("CT1")}
                  className={`vcis-button ${
                    assessmentType === "CT1" ? "vcis-button-primary" : "vcis-button-secondary"
                  }`}
                  style={{ justifyContent: "center" }}
                >
                  CT1 (Cycle Test 1)
                </button>
                <button
                  type="button"
                  id="type-assignment"
                  onClick={() => handleTypeChange("ASSIGNMENT")}
                  className={`vcis-button ${
                    assessmentType === "ASSIGNMENT" ? "vcis-button-primary" : "vcis-button-secondary"
                  }`}
                  style={{ justifyContent: "center" }}
                >
                  Continuous Assignment
                </button>
              </div>
            </div>

            {/* Assessment Name */}
            <div>
              <label htmlFor="assessment-name" className="vcis-label">
                Assessment Name / Title <span style={{ color: "var(--vcis-danger)" }}>*</span>
              </label>
              <input
                type="text"
                id="assessment-name"
                value={assessmentName}
                onChange={(e) => setAssessmentName(e.target.value)}
                placeholder="e.g., CT1, Assignment 1, Quiz 1..."
                className="vcis-input"
                disabled={isSubmitting}
                required
                maxLength={150}
              />
            </div>

            {/* Marks Grid */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "var(--space-3)",
              }}
            >
              <div>
                <label htmlFor="assessment-max-marks" className="vcis-label">
                  Maximum Marks <span style={{ color: "var(--vcis-danger)" }}>*</span>
                </label>
                <input
                  type="number"
                  id="assessment-max-marks"
                  value={isNaN(maxMarks) ? "" : maxMarks}
                  onChange={(e) => setMaxMarks(parseFloat(e.target.value))}
                  min={1}
                  max={1000}
                  className="vcis-input"
                  disabled={isSubmitting}
                  required
                />
              </div>

              <div>
                <label htmlFor="assessment-obtained-marks" className="vcis-label">
                  Obtained Marks <span style={{ color: "var(--vcis-danger)" }}>*</span>
                </label>
                <input
                  type="number"
                  id="assessment-obtained-marks"
                  value={isNaN(obtainedMarks) ? "" : obtainedMarks}
                  onChange={(e) => setObtainedMarks(parseFloat(e.target.value))}
                  min={0}
                  max={maxMarks || 1000}
                  className="vcis-input"
                  disabled={isSubmitting}
                  required
                />
              </div>
            </div>

            {/* Assessment Date */}
            <div>
              <label htmlFor="assessment-date" className="vcis-label">
                Evaluation Date <span style={{ color: "var(--vcis-danger)" }}>*</span>
              </label>
              <input
                type="date"
                id="assessment-date"
                value={assessmentDate}
                onChange={(e) => setAssessmentDate(e.target.value)}
                className="vcis-input"
                disabled={isSubmitting}
                required
              />
            </div>

            {/* Remarks */}
            <div>
              <label htmlFor="assessment-remarks" className="vcis-label">
                Remarks (Optional)
              </label>
              <textarea
                id="assessment-remarks"
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                rows={2}
                placeholder="Optional notes or evaluation comments..."
                className="vcis-input"
                style={{ width: "100%", resize: "vertical" }}
                disabled={isSubmitting}
                maxLength={1000}
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
              id="submit-assessment-btn"
              disabled={isSubmitting || enrollments.length === 0}
              className="vcis-button vcis-button-primary"
            >
              {isSubmitting ? "Saving..." : "Save Assessment Marks"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AssessmentEntryModal;
