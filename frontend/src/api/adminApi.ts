import apiClient from "./client";
import type { DepartmentInfo, CourseInfo, StudentProfile } from "./studentApi";
import type { FacultyProfile } from "./facultyApi";
import type { InterventionResponse } from "./interventionApi";
import type { PredictionResultState } from "./predictionApi";
import { getStudentPrediction } from "./predictionApi";

export interface SubjectInfo {
  id: number;
  course_id: number;
  name: string;
  code: string;
  semester: number;
  credits: number;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminProfile {
  user_id: number;
  email: string;
  role: "admin";
  designation: string;
}

export type UserRole = "student" | "faculty" | "hod" | "admin";

export interface CreateUserRequest {
  email: string;
  password: string;
  role: UserRole;
}

export interface UserResponse {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
}

/**
 * Resolve authenticated administrator profile.
 */
export async function getAdminProfile(
  userId: number,
  email: string
): Promise<AdminProfile> {
  return {
    user_id: userId,
    email,
    role: "admin",
    designation: "Institutional System Administrator",
  };
}

/**
 * Fetch all departments across the institution.
 */
export async function getSystemDepartments(): Promise<DepartmentInfo[]> {
  const response = await apiClient.get<DepartmentInfo[]>("/api/v1/departments/");
  return response.data;
}

/**
 * Fetch all academic courses across the institution.
 */
export async function getSystemCourses(): Promise<CourseInfo[]> {
  const response = await apiClient.get<CourseInfo[]>("/api/v1/courses/");
  return response.data;
}

/**
 * Fetch all subjects / curriculum modules across the institution.
 */
export async function getSystemSubjects(): Promise<SubjectInfo[]> {
  const response = await apiClient.get<SubjectInfo[]>("/api/v1/subjects/");
  return response.data;
}

/**
 * Fetch all faculty profiles across the institution.
 */
export async function getSystemFaculty(): Promise<FacultyProfile[]> {
  const response = await apiClient.get<FacultyProfile[]>("/api/v1/faculty/");
  return response.data;
}

/**
 * Fetch all student profiles across the institution.
 */
export async function getSystemStudents(): Promise<StudentProfile[]> {
  const response = await apiClient.get<StudentProfile[]>("/api/v1/students/");
  return response.data;
}

/**
 * Fetch all intervention records across the institution.
 */
export async function getSystemInterventions(): Promise<InterventionResponse[]> {
  const response = await apiClient.get<InterventionResponse[]>("/api/v1/interventions/");
  return response.data;
}

/**
 * Provision a new user account with role in the system.
 */
export async function createUserAccount(
  payload: CreateUserRequest
): Promise<UserResponse> {
  const response = await apiClient.post<UserResponse>("/api/v1/users/", payload);
  return response.data;
}

/**
 * On-demand score prediction for individual student review (decision support).
 */
export async function getStudentPredictionForAdmin(
  studentId: number,
  semester: number
): Promise<PredictionResultState> {
  return getStudentPrediction(studentId, semester);
}

/**
 * Fetch all user accounts across the institution (Admin only).
 */
export async function getSystemUsers(): Promise<UserResponse[]> {
  const response = await apiClient.get<UserResponse[]>("/api/v1/users/");
  return response.data;
}

export interface UpdateInterventionRequest {
  status?: string;
  action_plan?: string | null;
  follow_up_date?: string | null;
  description?: string | null;
}

/**
 * Update an intervention workflow record (Admin oversight).
 */
export async function updateSystemIntervention(
  id: number,
  payload: UpdateInterventionRequest
): Promise<InterventionResponse> {
  try {
    const response = await apiClient.patch<InterventionResponse>(
      `/api/v1/interventions/${id}`,
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
