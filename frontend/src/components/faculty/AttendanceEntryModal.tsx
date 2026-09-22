import React, { useState } from "react";
import type { AttendanceCreateRequest, AttendanceStatusType } from "../../api/facultyApi";
import type { EnrollmentResultResponse, StudentProfile } from "../../api/studentApi";

interface AttendanceEntryModalProps {
  student: StudentProfile;
  enrollments: EnrollmentResultResponse[];
  onSubmit: (payload: AttendanceCreateRequest) => Promise<void>;
  onClose: () => void;
  isSubmitting: boolean;
}

export const AttendanceEntryModal: React.FC<AttendanceEntryModalProps> = ({
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
  // Default to today's date in YYYY-MM-DD format
  const [attendanceDate, setAttendanceDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [status, setStatus] = useState<AttendanceStatusType>("PRESENT");
  const [remarks, setRemarks] = useState<string>("");
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!selectedEnrollmentId || selectedEnrollmentId <= 0) {
      setFormError("Please select an enrolled subject to record attendance.");
      return;
    }

    if (!attendanceDate) {
      setFormError("Please select a valid attendance date.");
      return;
    }

    if (remarks.length > 1000) {
      setFormError("Remarks cannot exceed 1000 characters.");
      return;
    }

    try {
      await onSubmit({
        enrollment_id: selectedEnrollmentId,
        attendance_date: attendanceDate,
        status: status,
        remarks: remarks.trim() ? remarks.trim() : null,
      });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message);
      } else {
        setFormError("Failed to record attendance. Please try again.");
      }
    }
  };

  return (
    <div className="vcis-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="attendance-modal-title">
      <div className="vcis-modal">
        {/* Header */}
        <div className="vcis-modal-header">
          <div>
            <h3 id="attendance-modal-title" className="vcis-modal-title">
              Record Attendance
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

        {/* Body */}
        <form onSubmit={handleSubmit}>
          <div className="vcis-modal-body" style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
            {formError && (
              <div className="vcis-error" role="alert">
                {formError}
              </div>
            )}

            {/* Subject Selector */}
            <div>
              <label
                htmlFor="attendance-subject"
                className="vcis-label"
              >
                Enrolled Subject <span style={{ color: "var(--vcis-danger)" }}>*</span>
              </label>
              <select
                id="attendance-subject"
                value={selectedEnrollmentId}
                onChange={(e) => setSelectedEnrollmentId(Number(e.target.value))}
                className="vcis-select"
                disabled={isSubmitting || enrollments.length === 0}
                required
              >
                {enrollments.length === 0 ? (
                  <option value={0}>No enrolled subjects found for this term</option>
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

            {/* Attendance Date */}
            <div>
              <label
                htmlFor="attendance-date"
                className="vcis-label"
              >
                Session Date <span style={{ color: "var(--vcis-danger)" }}>*</span>
              </label>
              <input
                type="date"
                id="attendance-date"
                value={attendanceDate}
                onChange={(e) => setAttendanceDate(e.target.value)}
                className="vcis-input"
                disabled={isSubmitting}
                required
              />
            </div>

            {/* Attendance Status */}
            <div>
              <label
                htmlFor="attendance-status"
                className="vcis-label"
              >
                Session Attendance Status <span style={{ color: "var(--vcis-danger)" }}>*</span>
              </label>
              <select
                id="attendance-status"
                value={status}
                onChange={(e) => setStatus(e.target.value as AttendanceStatusType)}
                className="vcis-select"
                disabled={isSubmitting}
                required
              >
                <option value="PRESENT">PRESENT</option>
                <option value="ABSENT">ABSENT</option>
              </select>
            </div>

            {/* Remarks */}
            <div>
              <label
                htmlFor="attendance-remarks"
                className="vcis-label"
              >
                Session Remarks (Optional)
              </label>
              <textarea
                id="attendance-remarks"
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                rows={3}
                placeholder="e.g., Lab practical session, verified lecture attendance..."
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
              id="submit-attendance-btn"
              disabled={isSubmitting || enrollments.length === 0}
              className="vcis-button vcis-button-primary"
            >
              {isSubmitting ? "Saving..." : "Save Attendance Record"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AttendanceEntryModal;
