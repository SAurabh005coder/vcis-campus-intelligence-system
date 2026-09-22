import apiClient from "./client";

export type InterventionType =
  | "extra_class"
  | "additional_assignment"
  | "counselling"
  | "monitoring"
  | string;

export type InterventionStatus =
  | "assigned"
  | "in_progress"
  | "completed"
  | "dismissed"
  | string;

export interface InterventionResponse {
  id: number;
  student_id: number;
  faculty_id: number;
  semester: number;
  intervention_type: InterventionType;
  status: InterventionStatus;
  trigger_predicted_score: number | null;
  trigger_academic_status: string | null;
  action_plan: string;
  follow_up_date: string | null;
  description?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Fetch interventions for the authenticated student.
 * The backend enforces student IDOR protection and automatically filters
 * to only the logged-in student's intervention records.
 */
export async function getMyInterventions(): Promise<InterventionResponse[]> {
  const response = await apiClient.get<InterventionResponse[]>("/api/v1/interventions/");
  return response.data;
}
