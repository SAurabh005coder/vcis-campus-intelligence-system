import apiClient from "./client";

export type AcademicStatus = "NORMAL" | "MONITOR" | "INTERVENTION";

export interface PredictionFeatures {
  current_attendance?: number;
  current_assignment_average?: number;
  current_ct1_average?: number;
  previous_semester_score?: number;
  previous_semester_attendance?: number;
  [key: string]: number | undefined;
}

export interface PredictionResponse {
  student_id: number;
  semester: number;
  predicted_final_semester_score: number;
  academic_status: AcademicStatus;
  model_version: string;
  model_type: string;
  scenario: string;
  features: PredictionFeatures;
}

export interface PredictionRequest {
  semester: number;
}

export interface PredictionResultState {
  data: PredictionResponse | null;
  insufficientData: boolean;
  errorMessage: string | null;
}

/**
 * Call the backend prediction endpoint for a given student and semester.
 * 
 * Contract:
 * POST /predictions/students/{student_id}
 * Body: { "semester": semester }
 */
export async function getStudentPrediction(
  studentId: number,
  semester: number
): Promise<PredictionResultState> {
  try {
    const response = await apiClient.post<PredictionResponse>(
      `/predictions/students/${studentId}`,
      { semester }
    );
    return {
      data: response.data,
      insufficientData: false,
      errorMessage: null,
    };
  } catch (error: unknown) {
    // Check if error is 422 Unprocessable Entity (Insufficient data)
    if (
      typeof error === "object" &&
      error !== null &&
      "response" in error &&
      typeof (error as { response?: { status?: number; data?: { detail?: string } } }).response ===
        "object"
    ) {
      const errResp = (
        error as { response?: { status?: number; data?: { detail?: string } } }
      ).response;
      if (errResp?.status === 422) {
        return {
          data: null,
          insufficientData: true,
          errorMessage:
            errResp.data?.detail ||
            "Prediction is not available yet because sufficient academic data is required.",
        };
      }
      return {
        data: null,
        insufficientData: false,
        errorMessage: errResp?.data?.detail || "Failed to load prediction.",
      };
    }

    return {
      data: null,
      insufficientData: false,
      errorMessage: "Could not connect to prediction service.",
    };
  }
}
