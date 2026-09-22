import apiClient from "./client";
import type { DepartmentInfo, CourseInfo, StudentProfile } from "./studentApi";
import type { PredictionResultState } from "./predictionApi";
import { getStudentPrediction } from "./predictionApi";
import type { InterventionResponse } from "./interventionApi";
import type {
  FacultyProfile,
  CreateInterventionRequest,
  UpdateInterventionRequest,
  InterventionFilterParams,
} from "./facultyApi";

export interface HodProfile {
  user_id: number;
  email: string;
  faculty_id?: number | null;
  department_id?: number | null;
  name?: string;
  designation?: string;
  employee_code?: string;
}

/**
 * Fetch HOD profile information:
 * Resolves optional Faculty record matching user_id.
 */
export async function getCurrentHodProfile(
  userId: number,
  email: string
): Promise<HodProfile> {
  try {
    const response = await apiClient.get<FacultyProfile[]>("/api/v1/faculty/");
    const matched = response.data.find((f) => f.user_id === userId);
    if (matched) {
      return {
        user_id: userId,
        email,
        faculty_id: matched.id,
        department_id: matched.department_id,
        name: `${matched.first_name} ${matched.last_name}`,
        designation: matched.designation || "Head of Department",
        employee_code: matched.employee_code,
      };
    }
  } catch {
    // Graceful fallback if faculty endpoint fails or user has no faculty row
  }

  return {
    user_id: userId,
    email,
    faculty_id: null,
    department_id: null,
    name: "Head of Department",
    designation: "Head of Department",
  };
}

/**
 * Fetch all departments.
 */
export async function getDepartments(): Promise<DepartmentInfo[]> {
  const response = await apiClient.get<DepartmentInfo[]>("/api/v1/departments/");
  return response.data;
}

/**
 * Fetch list of faculty members.
 */
export async function getFacultyList(): Promise<FacultyProfile[]> {
  const response = await apiClient.get<FacultyProfile[]>("/api/v1/faculty/");
  return response.data;
}

/**
 * Fetch all academic courses.
 */
export async function getCourses(): Promise<CourseInfo[]> {
  const response = await apiClient.get<CourseInfo[]>("/api/v1/courses/");
  return response.data;
}

/**
 * Fetch students accessible to HOD (scoped to HOD's department by backend).
 */
export async function getStudents(): Promise<StudentProfile[]> {
  const response = await apiClient.get<StudentProfile[]>("/api/v1/students/");
  return response.data;
}

/**
 * Fetch interventions accessible to HOD (scoped to HOD's department by backend).
 */
export async function getInterventions(
  params?: InterventionFilterParams
): Promise<InterventionResponse[]> {
  const response = await apiClient.get<InterventionResponse[]>(
    "/api/v1/interventions/",
    { params }
  );
  return response.data;
}

/**
 * Run early score prediction inference on-demand for a student.
 */
export async function getStudentPredictionForHod(
  studentId: number,
  semester: number
): Promise<PredictionResultState> {
  return getStudentPrediction(studentId, semester);
}

/**
 * Create an academic intervention (HOD role authorized).
 */
export async function createHodIntervention(
  payload: CreateInterventionRequest
): Promise<InterventionResponse> {
  const response = await apiClient.post<InterventionResponse>(
    "/api/v1/interventions/",
    payload
  );
  return response.data;
}

/**
 * Update intervention workflow status or action plan.
 * Historical trigger evidence fields remain immutable.
 */
export async function updateHodIntervention(
  interventionId: number,
  payload: UpdateInterventionRequest
): Promise<InterventionResponse> {
  const response = await apiClient.patch<InterventionResponse>(
    `/api/v1/interventions/${interventionId}`,
    payload
  );
  return response.data;
}
