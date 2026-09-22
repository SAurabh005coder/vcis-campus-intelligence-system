import React from "react";
import type { AcademicStatus, PredictionResponse } from "../../api/predictionApi";

interface FacultyPredictionCardProps {
  prediction: PredictionResponse | null;
  isLoading: boolean;
  insufficientData: boolean;
  errorMessage: string | null;
  onGeneratePrediction: () => void;
  onOpenInterventionModal: () => void;
  selectedStudentId: number | null;
}

export const FacultyPredictionCard: React.FC<FacultyPredictionCardProps> = ({
  prediction,
  isLoading,
  insufficientData,
  errorMessage,
  onGeneratePrediction,
  onOpenInterventionModal,
  selectedStudentId,
}) => {
  const getStatusConfig = (status: AcademicStatus) => {
    switch (status) {
      case "NORMAL":
        return {
          label: "NORMAL",
          badgeClass: "vcis-status-normal",
          scoreColor: "var(--vcis-status-normal-text)",
          explanation: "Student is academically on track (predicted score ≥ 60%). No immediate intervention needed.",
        };
      case "MONITOR":
        return {
          label: "MONITOR",
          badgeClass: "vcis-status-monitor",
          scoreColor: "var(--vcis-status-monitor-text)",
          explanation: "Borderline performance (50% – 59.9%). Faculty monitoring or guidance recommended.",
        };
      case "INTERVENTION":
        return {
          label: "INTERVENTION",
          badgeClass: "vcis-status-intervention",
          scoreColor: "var(--vcis-status-intervention-text)",
          explanation: "Predicted score is below 50%. Remedial support, additional assignments, or academic counselling required.",
        };
      default:
        return {
          label: status,
          badgeClass: "vcis-status-neutral",
          scoreColor: "var(--vcis-text)",
          explanation: "Academic classification status.",
        };
    }
  };

  return (
    <div className="vcis-hero-prediction">
      {/* Top Header of Card */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "var(--space-3)",
          marginBottom: "var(--space-5)",
        }}
      >
        <div>
          <div className="vcis-prediction-label" style={{ color: "var(--vcis-accent)" }}>
            Academic Intelligence
          </div>
          <h2
            style={{
              margin: "0.25rem 0 0 0",
              fontSize: "var(--font-xl)",
              fontWeight: "var(--font-weight-bold)",
              color: "var(--vcis-text)",
              letterSpacing: "-0.02em",
            }}
          >
            Early Academic Prediction
          </h2>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
          <button
            type="button"
            onClick={onGeneratePrediction}
            disabled={isLoading || !selectedStudentId}
            className="vcis-button vcis-button-primary vcis-button-sm"
            title="Generate or refresh early academic prediction for selected student"
          >
            {isLoading
              ? "Running Inference..."
              : prediction
              ? "Refresh Prediction"
              : "Generate Early Prediction"}
          </button>

          {prediction && (
            <button
              type="button"
              onClick={onOpenInterventionModal}
              className={`vcis-button vcis-button-sm ${
                prediction.academic_status === "INTERVENTION"
                  ? "vcis-button-danger"
                  : prediction.academic_status === "MONITOR"
                  ? "vcis-button-secondary"
                  : "vcis-button-ghost"
              }`}
              style={
                prediction.academic_status === "INTERVENTION"
                  ? { backgroundColor: "var(--vcis-danger)", color: "#ffffff", borderColor: "var(--vcis-danger)" }
                  : undefined
              }
              title="Assign an academic intervention to this student"
            >
              + Assign Intervention
            </button>
          )}
        </div>
      </div>

      {/* State Rendering */}
      {isLoading ? (
        <div className="vcis-loading" style={{ padding: "var(--space-8) 0" }}>
          <div className="vcis-spinner" aria-hidden="true" />
          <span style={{ fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)" }}>
            Evaluating academic prediction for selected student...
          </span>
        </div>
      ) : insufficientData ? (
        <div
          className="vcis-empty"
          style={{
            textAlign: "left",
            padding: "var(--space-6)",
            backgroundColor: "var(--vcis-surface-raised)",
            borderColor: "var(--vcis-border-strong)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-2)" }}>
            <span style={{ color: "var(--vcis-info)", fontSize: "1.25rem" }}>ℹ</span>
            <strong style={{ color: "var(--vcis-text)" }}>Prediction is not available yet</strong>
          </div>
          <p style={{ margin: 0, fontSize: "var(--font-sm)", color: "var(--vcis-text-secondary)", lineHeight: 1.5 }}>
            {errorMessage ||
              "Sufficient academic records (attendance, continuous assignments, and CT1 milestone) are required before early prediction can be evaluated."}
          </p>
        </div>
      ) : errorMessage ? (
        <div className="vcis-error" role="alert">
          <div style={{ fontWeight: "var(--font-weight-semibold)", marginBottom: "0.25rem" }}>
            Prediction Notice
          </div>
          <div>{errorMessage}</div>
        </div>
      ) : prediction ? (
        <div>
          {/* Main Prediction Grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "var(--space-5)",
              alignItems: "center",
              marginBottom: "var(--space-5)",
            }}
          >
            {/* Primary Predicted Score */}
            <div>
              <div className="vcis-prediction-label">
                Predicted Final Semester Score
              </div>
              <div className="vcis-hero-prediction-score">
                <span style={{ color: getStatusConfig(prediction.academic_status).scoreColor }}>
                  {prediction.predicted_final_semester_score.toFixed(2)}
                </span>
                <span className="vcis-hero-prediction-denominator">/ 100</span>
              </div>
              <p
                style={{
                  margin: 0,
                  fontSize: "var(--font-sm)",
                  color: "var(--vcis-text-secondary)",
                }}
              >
                Target semester: Semester {prediction.semester}
              </p>
            </div>

            {/* Academic Status Card */}
            {(() => {
              const statusCfg = getStatusConfig(prediction.academic_status);
              return (
                <div
                  style={{
                    backgroundColor: "var(--vcis-surface-raised)",
                    border: "1px solid var(--vcis-border-strong)",
                    borderRadius: "var(--radius-lg)",
                    padding: "var(--space-5)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: "var(--space-3)",
                    }}
                  >
                    <span className="vcis-prediction-label">Academic Status</span>
                    <span className={`vcis-status ${statusCfg.badgeClass}`}>
                      {statusCfg.label}
                    </span>
                  </div>
                  <p
                    style={{
                      margin: 0,
                      fontSize: "var(--font-sm)",
                      color: "var(--vcis-text)",
                      lineHeight: 1.5,
                    }}
                  >
                    {statusCfg.explanation}
                  </p>
                </div>
              );
            })()}
          </div>

          {/* Model Metadata Footer */}
          <div
            style={{
              padding: "var(--space-3) var(--space-4)",
              backgroundColor: "var(--vcis-surface-raised)",
              border: "1px solid var(--vcis-border)",
              borderRadius: "var(--radius-md)",
              fontSize: "var(--font-xs)",
              color: "var(--vcis-text-secondary)",
              display: "flex",
              flexWrap: "wrap",
              gap: "var(--space-4)",
              alignItems: "center",
            }}
          >
            <div>
              <strong style={{ color: "var(--vcis-text)" }}>Model:</strong> {prediction.model_type} ({prediction.model_version})
            </div>
            <div>
              <strong style={{ color: "var(--vcis-text)" }}>Scenario:</strong> {prediction.scenario}
            </div>
          </div>
        </div>
      ) : (
        <div className="vcis-empty">
          Click <strong>&quot;Generate Early Prediction&quot;</strong> to evaluate academic indicators for the selected student.
        </div>
      )}
    </div>
  );
};

export default FacultyPredictionCard;
