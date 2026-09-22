import React, { useState } from "react";
import type { StudentProfile, DepartmentInfo } from "../../api/studentApi";
import type { PredictionResponse } from "../../api/predictionApi";
import type { InterventionResponse } from "../../api/interventionApi";
import type {
  InterventionStatus,
  UpdateInterventionRequest,
} from "../../api/facultyApi";

interface HodStudentReviewProps {
  student: StudentProfile;
  department: DepartmentInfo | null;
  prediction: PredictionResponse | null;
  isPredictionLoading: boolean;
  insufficientData: boolean;
  predictionError: string | null;
  onGeneratePrediction: () => void;
  interventions: InterventionResponse[];
  isInterventionsLoading: boolean;
  onUpdateIntervention: (
    id: number,
    payload: UpdateInterventionRequest
  ) => Promise<void>;
  onOpenInterventionModal: () => void;
}

export const HodStudentReview: React.FC<HodStudentReviewProps> = ({
  student,
  department,
  prediction,
  isPredictionLoading,
  insufficientData,
  predictionError,
  onGeneratePrediction,
  interventions,
  isInterventionsLoading,
  onUpdateIntervention,
  onOpenInterventionModal,
}) => {
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const formatPercentage = (val?: number | null) => {
    if (val === undefined || val === null || isNaN(val)) {
      return "Not available";
    }
    return `${val.toFixed(2)}%`;
  };

  const handleStatusChange = async (
    intervention: InterventionResponse,
    newStatus: InterventionStatus
  ) => {
    setUpdatingId(intervention.id);
    try {
      await onUpdateIntervention(intervention.id, { status: newStatus });
    } finally {
      setUpdatingId(null);
    }
  };

  const features = prediction?.features;

  const getStatusClass = (status: string) => {
    switch (status?.toUpperCase()) {
      case "NORMAL":
        return "vcis-status-normal";
      case "MONITOR":
        return "vcis-status-monitor";
      case "INTERVENTION":
        return "vcis-status-intervention";
      default:
        return "vcis-status-neutral";
    }
  };

  return (
    <div className="vcis-card">
      <div className="vcis-card-header">
        <div>
          <span
            style={{
              fontSize: "var(--vcis-font-size-xs)",
              fontWeight: "var(--vcis-font-weight-bold)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--vcis-accent)",
              display: "block",
              marginBottom: "var(--space-1)",
            }}
          >
            Student Academic Inspection
          </span>
          <h2 className="vcis-card-title" style={{ fontSize: "var(--vcis-font-size-xl)" }}>
            {student.name}
          </h2>
          <p className="vcis-card-subtitle">
            Roll No: <strong style={{ color: "var(--vcis-text)" }}>{student.roll_number}</strong> • ID: #{student.id} • Dept:{" "}
            <strong style={{ color: "var(--vcis-text)" }}>{department?.name || `Dept #${student.department_id}`}</strong> • Current
            Semester: <strong style={{ color: "var(--vcis-text)" }}>Sem {student.current_semester}</strong> • Email: {student.email}
          </p>
        </div>

        {/* Prediction Trigger Action */}
        <button
          id="hod-generate-prediction-btn"
          onClick={onGeneratePrediction}
          disabled={isPredictionLoading}
          className="vcis-btn vcis-btn-primary"
          style={{ whiteSpace: "nowrap" }}
        >
          {isPredictionLoading ? "Evaluating Model..." : "Generate Early Prediction"}
        </button>
      </div>

      <div className="vcis-card-body">
        {/* Prediction Error / Insufficient Data */}
        {predictionError && (
          <div className="vcis-alert vcis-alert-danger" style={{ marginBottom: "var(--space-4)" }}>
            {predictionError}
          </div>
        )}

        {insufficientData && (
          <div className="vcis-alert vcis-alert-warning" style={{ marginBottom: "var(--space-4)" }}>
            ⚠️ <strong>Insufficient Academic Records:</strong> The backend was unable to extract enough feature data to evaluate a complete ML prediction for Semester {student.current_semester}.
          </div>
        )}

        {/* Extracted Academic Indicators */}
        <div style={{ marginBottom: "var(--space-6)" }}>
          <h4
            style={{
              margin: "0 0 var(--space-3) 0",
              fontSize: "var(--vcis-font-size-sm)",
              fontWeight: "var(--vcis-font-weight-semibold)",
              color: "var(--vcis-text-secondary)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Academic Indicators (Semester {student.current_semester})
          </h4>

          {isPredictionLoading ? (
            <div className="vcis-empty-state" style={{ padding: "var(--space-4)" }}>
              <p className="vcis-empty-text">Extracting academic features from database records...</p>
            </div>
          ) : features ? (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                gap: "var(--space-3)",
              }}
            >
              <div className="vcis-kpi-card">
                <div>
                  <div className="vcis-kpi-value">
                    {formatPercentage(features.current_attendance)}
                  </div>
                  <div className="vcis-kpi-label">Current Attendance</div>
                </div>
                <div className="vcis-kpi-context">Recorded term attendance</div>
              </div>

              <div className="vcis-kpi-card">
                <div>
                  <div className="vcis-kpi-value">
                    {formatPercentage(features.current_assignment_average)}
                  </div>
                  <div className="vcis-kpi-label">Assignment Avg</div>
                </div>
                <div className="vcis-kpi-context">Continuous evaluation</div>
              </div>

              <div className="vcis-kpi-card">
                <div>
                  <div className="vcis-kpi-value">
                    {formatPercentage(features.current_ct1_average)}
                  </div>
                  <div className="vcis-kpi-label">CT-1 Average</div>
                </div>
                <div className="vcis-kpi-context">Cycle test 1 milestone</div>
              </div>

              {student.current_semester > 1 && (
                <>
                  <div className="vcis-kpi-card">
                    <div>
                      <div className="vcis-kpi-value">
                        {formatPercentage(features.previous_semester_score)}
                      </div>
                      <div className="vcis-kpi-label">Prev Sem Score</div>
                    </div>
                    <div className="vcis-kpi-context">Sem {student.current_semester - 1} final</div>
                  </div>

                  <div className="vcis-kpi-card">
                    <div>
                      <div className="vcis-kpi-value">
                        {formatPercentage(features.previous_semester_attendance)}
                      </div>
                      <div className="vcis-kpi-label">Prev Sem Attendance</div>
                    </div>
                    <div className="vcis-kpi-context">Sem {student.current_semester - 1}</div>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="vcis-empty-state" style={{ padding: "var(--space-4)" }}>
              <p className="vcis-empty-text">
                Academic indicators are extracted from verified database records upon clicking <strong>&quot;Generate Early Prediction&quot;</strong>.
              </p>
            </div>
          )}
        </div>

        {/* Prediction Output & Academic Status Hero */}
        {prediction && (
          <div
            style={{
              backgroundColor: "var(--vcis-surface-soft)",
              borderRadius: "var(--radius-lg)",
              border: "1px solid var(--vcis-border)",
              padding: "var(--space-5)",
              marginBottom: "var(--space-6)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "var(--space-4)",
                marginBottom: "var(--space-3)",
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: "var(--vcis-font-size-xs)",
                    color: "var(--vcis-text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    fontWeight: "var(--vcis-font-weight-semibold)",
                  }}
                >
                  Machine Learning Early Prediction
                </span>
                <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-4)", marginTop: "var(--space-2)" }}>
                  <span style={{ fontSize: "2rem", fontWeight: "var(--vcis-font-weight-extrabold)", color: "var(--vcis-accent)" }}>
                    {prediction.predicted_final_semester_score.toFixed(2)}%
                  </span>
                  <span className={`vcis-status ${getStatusClass(prediction.academic_status)}`}>
                    {prediction.academic_status}
                  </span>
                </div>
              </div>

              <button
                id="hod-assign-intervention-btn"
                onClick={onOpenInterventionModal}
                className="vcis-btn vcis-btn-primary"
                style={{
                  backgroundColor: "var(--vcis-success)",
                  borderColor: "var(--vcis-success)",
                }}
              >
                + Assign Academic Intervention
              </button>
            </div>

            <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
              Model Metadata: Type: <code>{prediction.model_type}</code> • Version: <code>{prediction.model_version}</code> • Scenario: <code>{prediction.scenario}</code> • Target Semester: Sem {prediction.semester}
            </div>
          </div>
        )}

        {/* Student's Academic Interventions Section */}
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "var(--space-3)",
            }}
          >
            <h4
              style={{
                margin: 0,
                fontSize: "var(--vcis-font-size-sm)",
                fontWeight: "var(--vcis-font-weight-semibold)",
                color: "var(--vcis-text-secondary)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Active Academic Interventions ({interventions.length})
            </h4>
            <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
              Historical trigger evidence is immutable
            </span>
          </div>

          {isInterventionsLoading ? (
            <div className="vcis-empty-state" style={{ padding: "var(--space-4)" }}>
              <p className="vcis-empty-text">Loading student interventions...</p>
            </div>
          ) : interventions.length === 0 ? (
            <div className="vcis-empty-state" style={{ padding: "var(--space-4)" }}>
              <p className="vcis-empty-title">No Recorded Interventions</p>
              <p className="vcis-empty-text">No active interventions recorded for {student.name}.</p>
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-3)",
              }}
            >
              {interventions.map((interv) => {
                const statusCls = getStatusClass(interv.trigger_academic_status || "NORMAL");
                const isUpdating = updatingId === interv.id;

                return (
                  <div
                    key={interv.id}
                    style={{
                      backgroundColor: "var(--vcis-surface-soft)",
                      borderRadius: "var(--radius-md)",
                      border: "1px solid var(--vcis-border)",
                      padding: "var(--space-4)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        flexWrap: "wrap",
                        gap: "var(--space-2)",
                        marginBottom: "var(--space-3)",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                        <strong style={{ fontSize: "var(--vcis-font-size-sm)", color: "var(--vcis-text)" }}>
                          {interv.intervention_type.replace("_", " ").toUpperCase()}
                        </strong>
                        <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
                          • Semester {interv.semester}
                        </span>
                      </div>

                      {/* Workflow Status Modifier */}
                      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                        <span style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>Workflow:</span>
                        <select
                          disabled={isUpdating}
                          value={interv.status.toLowerCase()}
                          onChange={(e) =>
                            handleStatusChange(
                              interv,
                              e.target.value as InterventionStatus
                            )
                          }
                          className="vcis-form-select"
                          style={{
                            padding: "0.2rem 0.5rem",
                            fontSize: "var(--vcis-font-size-xs)",
                            fontWeight: "var(--vcis-font-weight-semibold)",
                            width: "auto",
                          }}
                        >
                          <option value="assigned">Assigned</option>
                          <option value="in_progress">In Progress</option>
                          <option value="completed">Completed</option>
                          <option value="dismissed">Dismissed</option>
                        </select>
                      </div>
                    </div>

                    {/* Read-Only Historical Trigger Evidence */}
                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: "var(--space-4)",
                        fontSize: "var(--vcis-font-size-xs)",
                        color: "var(--vcis-text-secondary)",
                        backgroundColor: "var(--vcis-surface-muted)",
                        padding: "var(--space-2) var(--space-3)",
                        borderRadius: "var(--radius-sm)",
                        marginBottom: "var(--space-2)",
                      }}
                    >
                      <div>
                        <span>Historical Trigger Score: </span>
                        <strong style={{ color: "var(--vcis-text)" }}>
                          {interv.trigger_predicted_score !== null && interv.trigger_predicted_score !== undefined
                            ? `${interv.trigger_predicted_score.toFixed(2)}%`
                            : "N/A"}
                        </strong> (Immutable)
                      </div>
                      <div>
                        <span>Trigger Status: </span>
                        <span className={`vcis-status ${statusCls}`} style={{ padding: "0.1rem 0.4rem", fontSize: "0.7rem" }}>
                          {interv.trigger_academic_status || "NORMAL"}
                        </span>
                      </div>
                      <div>
                        <span>Faculty ID: </span>
                        <strong style={{ color: "var(--vcis-text)" }}>#{interv.faculty_id}</strong>
                      </div>
                    </div>

                    {interv.action_plan && (
                      <div style={{ fontSize: "var(--vcis-font-size-sm)", color: "var(--vcis-text)", marginBottom: "var(--space-2)" }}>
                        <strong>Action Plan:</strong> {interv.action_plan}
                      </div>
                    )}

                    {(interv.description || interv.notes) && (
                      <div style={{ fontSize: "var(--vcis-font-size-xs)", color: "var(--vcis-text-muted)" }}>
                        <strong>Notes:</strong> {interv.description || interv.notes}
                      </div>
                    )}

                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        fontSize: "var(--vcis-font-size-xs)",
                        color: "var(--vcis-text-muted)",
                        marginTop: "var(--space-2)",
                      }}
                    >
                      <span>Created: {new Date(interv.created_at).toLocaleDateString()}</span>
                      {interv.follow_up_date && (
                        <span>Follow-up: {interv.follow_up_date}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
