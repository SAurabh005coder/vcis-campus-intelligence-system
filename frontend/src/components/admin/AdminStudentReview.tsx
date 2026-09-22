import React from "react";
import type { StudentProfile, DepartmentInfo, CourseInfo } from "../../api/studentApi";
import type { PredictionResponse } from "../../api/predictionApi";
import type { InterventionResponse } from "../../api/interventionApi";

interface AdminStudentReviewProps {
  student: StudentProfile;
  department: DepartmentInfo | null;
  course: CourseInfo | null;
  prediction: PredictionResponse | null;
  isPredictionLoading: boolean;
  insufficientData: boolean;
  predictionError: string | null;
  onGeneratePrediction: () => void;
  interventions: InterventionResponse[];
  isInterventionsLoading: boolean;
  onClose: () => void;
}

export const AdminStudentReview: React.FC<AdminStudentReviewProps> = ({
  student,
  department,
  course,
  prediction,
  isPredictionLoading,
  insufficientData,
  predictionError,
  onGeneratePrediction,
  interventions,
  isInterventionsLoading,
  onClose,
}) => {
  const formatPercentage = (val?: number | null) => {
    if (val === undefined || val === null || isNaN(val)) {
      return "Not available";
    }
    return `${val.toFixed(2)}%`;
  };

  const getStatusClass = (status: string) => {
    switch (status.toUpperCase()) {
      case "NORMAL":
        return "vcis-status-normal";
      case "MONITOR":
        return "vcis-status-monitor";
      case "INTERVENTION":
        return "vcis-status-intervention";
      default:
        return "vcis-badge-neutral";
    }
  };

  const features = prediction?.features;

  return (
    <div className="vcis-card" style={{ marginBottom: "var(--space-6)", borderLeft: "4px solid var(--vcis-primary)" }}>
      {/* Header */}
      <div className="vcis-card-header">
        <div>
          <span
            style={{
              fontSize: "var(--vcis-font-size-xs)",
              fontWeight: "var(--vcis-font-weight-bold)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--vcis-primary)",
            }}
          >
            Administrative Student Inspection
          </span>
          <h3 style={{ margin: "var(--space-1) 0 0 0", fontSize: "var(--vcis-font-size-lg)", fontWeight: "var(--vcis-font-weight-bold)", color: "var(--vcis-text)" }}>
            {student.name}
          </h3>
          <p style={{ margin: "var(--space-1) 0 0 0", fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-secondary)" }}>
            Roll No: <strong>{student.roll_number}</strong> • ID: #{student.id} • Dept:{" "}
            <strong>{department?.name || `Dept #${student.department_id}`}</strong> • Course:{" "}
            <strong>{course?.name || `Course #${student.course_id}`}</strong> • Semester:{" "}
            <strong>Sem {student.current_semester}</strong> • Email: {student.email}
          </p>
        </div>

        <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center" }}>
          <button
            id="admin-evaluate-prediction-btn"
            onClick={onGeneratePrediction}
            disabled={isPredictionLoading}
            className="vcis-btn vcis-btn-primary"
          >
            {isPredictionLoading ? "Evaluating..." : "Evaluate Early Prediction"}
          </button>
          <button
            id="admin-close-review-btn"
            onClick={onClose}
            className="vcis-btn vcis-btn-secondary"
          >
            Close
          </button>
        </div>
      </div>

      <div className="vcis-card-body">
        {/* Errors / Insufficient Data */}
        {predictionError && (
          <div className="vcis-alert vcis-alert-danger" style={{ marginBottom: "var(--space-4)" }}>
            ✕ {predictionError}
          </div>
        )}

        {insufficientData && (
          <div className="vcis-alert vcis-alert-warning" style={{ marginBottom: "var(--space-4)" }}>
            ⚠️ <strong>Insufficient Academic Records:</strong> The backend was unable to extract sufficient features to evaluate an early prediction for Semester {student.current_semester}.
          </div>
        )}

        {/* Academic Indicators */}
        <div style={{ marginBottom: "var(--space-5)" }}>
          <h4
            style={{
              margin: "0 0 var(--space-2) 0",
              fontSize: "var(--vcis-font-size-xs)",
              fontWeight: "var(--vcis-font-weight-semibold)",
              color: "var(--vcis-text-secondary)",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
            }}
          >
            Verified Academic Indicators (Semester {student.current_semester})
          </h4>

          {isPredictionLoading ? (
            <div style={{ padding: "var(--space-4)", textAlign: "center", color: "var(--vcis-text-muted)" }}>
              Extracting features from database records...
            </div>
          ) : features ? (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                gap: "var(--space-3)",
              }}
            >
              <div
                style={{
                  backgroundColor: "var(--vcis-surface-soft)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--vcis-border)",
                  padding: "var(--space-3) var(--space-4)",
                }}
              >
                <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>Attendance</div>
                <div
                  style={{
                    fontSize: "1.25rem",
                    fontWeight: 700,
                    color: "var(--vcis-text)",
                  }}
                >
                  {formatPercentage(features.current_attendance)}
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--vcis-text-muted)" }}>Current semester</div>
              </div>

              <div
                style={{
                  backgroundColor: "var(--vcis-surface-soft)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--vcis-border)",
                  padding: "var(--space-3) var(--space-4)",
                }}
              >
                <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>Assignment Avg</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--vcis-text)" }}>
                  {formatPercentage(features.current_assignment_average)}
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--vcis-text-muted)" }}>Coursework</div>
              </div>

              <div
                style={{
                  backgroundColor: "var(--vcis-surface-soft)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--vcis-border)",
                  padding: "var(--space-3) var(--space-4)",
                }}
              >
                <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>CT-1 Average</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--vcis-text)" }}>
                  {formatPercentage(features.current_ct1_average)}
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--vcis-text-muted)" }}>Early assessment</div>
              </div>

              {student.current_semester > 1 && (
                <>
                  <div
                    style={{
                      backgroundColor: "var(--vcis-surface-soft)",
                      borderRadius: "var(--radius-md)",
                      border: "1px dashed var(--vcis-border-strong)",
                      padding: "var(--space-3) var(--space-4)",
                    }}
                  >
                    <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>Prev Sem Score</div>
                    <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--vcis-text-secondary)" }}>
                      {formatPercentage(features.previous_semester_score)}
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "var(--vcis-text-muted)" }}>
                      Sem {student.current_semester - 1} final
                    </div>
                  </div>

                  <div
                    style={{
                      backgroundColor: "var(--vcis-surface-soft)",
                      borderRadius: "var(--radius-md)",
                      border: "1px dashed var(--vcis-border-strong)",
                      padding: "var(--space-3) var(--space-4)",
                    }}
                  >
                    <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>Prev Sem Attendance</div>
                    <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--vcis-text-secondary)" }}>
                      {formatPercentage(features.previous_semester_attendance)}
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "var(--vcis-text-muted)" }}>
                      Sem {student.current_semester - 1}
                    </div>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div
              style={{
                padding: "var(--space-4)",
                backgroundColor: "var(--vcis-surface-soft)",
                borderRadius: "var(--radius-md)",
                border: "1px dashed var(--vcis-border-strong)",
                color: "var(--vcis-text-muted)",
                fontSize: "var(--vcis-font-size-xs)",
              }}
            >
              Academic indicators are extracted from database records on demand upon clicking <strong>&quot;Evaluate Early Prediction&quot;</strong>.
            </div>
          )}
        </div>

        {/* Prediction Output */}
        {prediction && (
          <div
            style={{
              backgroundColor: "var(--vcis-surface-soft)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--vcis-border)",
              padding: "var(--space-4)",
              marginBottom: "var(--space-5)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "var(--space-3)",
                marginBottom: "var(--space-2)",
              }}
            >
              <div>
                <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  Predicted Final Semester Score
                </span>
                <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-3)", marginTop: "var(--space-1)" }}>
                  <span style={{ fontSize: "1.85rem", fontWeight: 800, color: "var(--vcis-text)" }}>
                    {prediction.predicted_final_semester_score.toFixed(2)}%
                  </span>
                  <span className={`vcis-status ${getStatusClass(prediction.academic_status)}`}>
                    {prediction.academic_status}
                  </span>
                </div>
              </div>
            </div>

            <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
              Model: <code>{prediction.model_type}</code> • Version: <code>{prediction.model_version}</code> • Scenario: <code>{prediction.scenario}</code>
            </div>
          </div>
        )}

        {/* Recorded Interventions */}
        <div>
          <h4
            style={{
              margin: "0 0 var(--space-2) 0",
              fontSize: "var(--vcis-font-size-xs)",
              fontWeight: "var(--vcis-font-weight-semibold)",
              color: "var(--vcis-text-secondary)",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
            }}
          >
            Recorded Interventions for Student ({interventions.length})
          </h4>

          {isInterventionsLoading ? (
            <div style={{ padding: "var(--space-3)", color: "var(--vcis-text-muted)", fontSize: "var(--vcis-font-size-xs)" }}>
              Loading interventions...
            </div>
          ) : interventions.length === 0 ? (
            <div
              style={{
                padding: "var(--space-4)",
                backgroundColor: "var(--vcis-surface-soft)",
                borderRadius: "var(--radius-md)",
                border: "1px dashed var(--vcis-border-strong)",
                color: "var(--vcis-text-muted)",
                fontSize: "var(--vcis-font-size-xs)",
              }}
            >
              No interventions on record for {student.name}.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
              {interventions.map((interv) => (
                <div
                  key={interv.id}
                  style={{
                    backgroundColor: "var(--vcis-surface)",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid var(--vcis-border)",
                    padding: "var(--space-3) var(--space-4)",
                    fontSize: "var(--vcis-font-size-xs)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-1)" }}>
                    <strong>
                      {interv.intervention_type.replace("_", " ").toUpperCase()} • Sem {interv.semester}
                    </strong>
                    <span className="vcis-badge vcis-badge-neutral">
                      {interv.status.replace("_", " ")}
                    </span>
                  </div>
                  <div style={{ color: "var(--vcis-text-secondary)" }}>
                    <span>Trigger: {interv.trigger_predicted_score?.toFixed(2) || "N/A"}%</span> •{" "}
                    <span>Status: {interv.trigger_academic_status || "NORMAL"}</span> •{" "}
                    <span>Faculty ID: #{interv.faculty_id}</span>
                  </div>
                  {interv.action_plan && (
                    <div style={{ marginTop: "var(--space-1)", color: "var(--vcis-text)" }}>
                      <strong>Plan:</strong> {interv.action_plan}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminStudentReview;
