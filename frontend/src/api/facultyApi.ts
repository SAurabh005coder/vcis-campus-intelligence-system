import apiClient from "./client";
import type { StudentProfile, DepartmentInfo, CourseInfo } from "./studentApi";
export type { CourseInfo, DepartmentInfo };
import type { PredictionResultState } from "./predictionApi";
import { getStudentPrediction } from "./predictionApi";
import type { InterventionResponse } from "./interventionApi";

export interface FacultyProfile {
  id: number;
  user_id: number;
  department_id: number;
  employee_code: string;
  first_name: string;
  last_name: string;
  designation: string;
  phone: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type InterventionType =
  | "extra_class"
  | "additional_assignment"
  | "counselling"
  | "monitoring";

export type InterventionStatus =
  | "assigned"
  | "in_progress"
  | "completed"
  | "dismissed";

export interface CreateInterventionRequest {
  student_id: number;
  faculty_id: number;
  semester: number;
  intervention_type: InterventionType;
  status?: InterventionStatus;
  trigger_predicted_score: number;
  trigger_academic_status: string;
  description?: string | null;
  action_plan?: string | null;
  follow_up_date?: string | null;
}

export interface UpdateInterventionRequest {
  status?: InterventionStatus;
  description?: string | null;
  action_plan?: string | null;
  follow_up_date?: string | null;
}

export interface InterventionFilterParams {
  student_id?: number;
  faculty_id?: number;
  semester?: number;
  status?: InterventionStatus;
}

/**
 * Fetch all faculty profiles and resolve the profile of the authenticated user.
 */
export async function getCurrentFacultyProfile(
  userId: number
): Promise<FacultyProfile | null> {
  const response = await apiClient.get<FacultyProfile[]>("/api/v1/faculty/");
  const matched = response.data.find((f) => f.user_id === userId);
  return matched || null;
}

/**
 * Fetch all students available in the system.
 */
export async function getAllStudents(): Promise<StudentProfile[]> {
  const response = await apiClient.get<StudentProfile[]>("/api/v1/students/");
  return response.data;
}

/**
 * Fetch department metadata.
 */
export async function getDepartmentById(
  departmentId: number
): Promise<DepartmentInfo | null> {
  try {
    const response = await apiClient.get<DepartmentInfo>(
      `/api/v1/departments/${departmentId}`
    );
    return response.data;
  } catch {
    return null;
  }
}

/**
 * Fetch course metadata.
 */
export async function getCourseById(
  courseId: number
): Promise<CourseInfo | null> {
  try {
    const response = await apiClient.get<CourseInfo>(
      `/api/v1/courses/${courseId}`
    );
    return response.data;
  } catch {
    return null;
  }
}

/**
 * Fetch all departments.
 */
export async function getDepartments(): Promise<DepartmentInfo[]> {
  const response = await apiClient.get<DepartmentInfo[]>("/api/v1/departments/");
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
 * Call ML prediction inference for the student and semester.
 */
export async function getStudentPredictionForFaculty(
  studentId: number,
  semester: number
): Promise<PredictionResultState> {
  return getStudentPrediction(studentId, semester);
}

/**
 * List interventions with optional filters (student_id, faculty_id, semester, status).
 */
export async function listInterventions(
  params?: InterventionFilterParams
): Promise<InterventionResponse[]> {
  const response = await apiClient.get<InterventionResponse[]>(
    "/api/v1/interventions/",
    { params }
  );
  return response.data;
}

/**
 * Explicitly create a new academic intervention assigned to a student.
 */
export async function createIntervention(
  payload: CreateInterventionRequest
): Promise<InterventionResponse> {
  try {
    const response = await apiClient.post<InterventionResponse>(
      "/api/v1/interventions/",
      payload
    );
    return response.data;
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })
      ?.response?.data?.detail;
    if (detail) {
      throw new Error(detail);
    }
    throw error;
  }
}

/**
 * Update workflow status, description, action plan, or follow-up date.
 * Historical trigger evidence fields are protected and not modifiable.
 */
export async function updateIntervention(
  interventionId: number,
  payload: UpdateInterventionRequest
): Promise<InterventionResponse> {
  try {
    const response = await apiClient.patch<InterventionResponse>(
      `/api/v1/interventions/${interventionId}`,
      payload
    );
    return response.data;
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })
      ?.response?.data?.detail;
    if (detail) {
      throw new Error(detail);
    }
    throw error;
  }
}

export type AttendanceStatusType = "PRESENT" | "ABSENT";

export interface AttendanceCreateRequest {
  enrollment_id: number;
  attendance_date: string; // YYYY-MM-DD
  status: AttendanceStatusType;
  remarks?: string | null;
}

export interface AttendanceRecordResponse {
  id: number;
  enrollment_id: number;
  attendance_date: string;
  status: AttendanceStatusType;
  remarks: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Record student attendance for an enrollment.
 * Contract: POST /api/v1/attendance/
 */
export async function createAttendanceRecord(
  payload: AttendanceCreateRequest
): Promise<AttendanceRecordResponse> {
  try {
    const formattedPayload = {
      ...payload,
      status: payload.status.toLowerCase(),
    };
    const response = await apiClient.post<AttendanceRecordResponse>(
      "/api/v1/attendance/",
      formattedPayload
    );
    return response.data;
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })
      ?.response?.data?.detail;
    if (detail) {
      throw new Error(detail);
    }
    throw error;
  }
}

export type AllowedAssessmentType = "CT1" | "ASSIGNMENT";

export interface AssessmentCreateRequest {
  enrollment_id: number;
  assessment_type: AllowedAssessmentType;
  assessment_name: string;
  max_marks: number;
  obtained_marks: number;
  assessment_date: string; // YYYY-MM-DD
  remarks?: string | null;
}

export interface AssessmentRecordResponse {
  id: number;
  enrollment_id: number;
  assessment_type: string;
  assessment_name: string;
  max_marks: number;
  obtained_marks: number;
  assessment_date: string;
  remarks: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Record student assessment (CT1 or Assignment) for an enrollment.
 * Contract: POST /api/v1/assessments/
 */
export async function createAssessmentRecord(
  payload: AssessmentCreateRequest
): Promise<AssessmentRecordResponse> {
  try {
    const formattedPayload = {
      ...payload,
      assessment_type: payload.assessment_type.toLowerCase(),
    };
    const response = await apiClient.post<AssessmentRecordResponse>(
      "/api/v1/assessments/",
      formattedPayload
    );
    return response.data;
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } })
      ?.response?.data?.detail;
    if (detail) {
      throw new Error(detail);
    }
    throw error;
  }
}
