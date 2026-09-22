import apiClient from "./client";

export interface StudentProfile {
  id: number;
  user_id: number;
  department_id: number;
  course_id: number;
  roll_number: string;
  admission_year: number;
  current_semester: number;
  name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CourseInfo {
  id: number;
  department_id: number;
  name: string;
  code: string;
  description?: string | null;
  duration_years: number;
  total_semesters: number;
  is_active: boolean;
}

export interface DepartmentInfo {
  id: number;
  name: string;
  code: string;
  description?: string | null;
  is_active: boolean;
}

export interface AssessmentResultItem {
  assessment_id: number;
  assessment_type: string;
  assessment_name: string;
  max_marks: number;
  obtained_marks: number;
  percentage: number;
}

export interface EnrollmentResultResponse {
  enrollment_id: number;
  student_id: number;
  subject_id: number;
  academic_year: string;
  subject_name: string | null;
  subject_code: string | null;
  semester: number | null;
  credits: number | null;
  total_max_marks: number;
  total_obtained_marks: number;
  overall_percentage: number;
  assessments: AssessmentResultItem[];
}

export interface StudentSemesterResultResponse {
  student_id: number;
  semester: number;
  total_subjects: number;
  total_credits: number;
  total_max_marks: number;
  total_obtained_marks: number;
  overall_percentage: number;
  subjects: EnrollmentResultResponse[];
}

export interface EnrollmentPerformanceProfileResponse {
  enrollment_id: number;
  student_id: number;
  subject_id: number;
  academic_year: string;
  subject_name: string | null;
  subject_code: string | null;
  semester: number | null;
  credits: number | null;
  assessment_percentage: number;
  attendance_percentage: number;
  total_classes: number;
  present_classes: number;
  absent_classes: number;
}

export interface StudentAcademicSummaryResponse {
  student_id: number;
  total_subjects: number;
  total_max_marks: number;
  total_obtained_marks: number;
  overall_percentage: number;
  subjects: EnrollmentResultResponse[];
}

/**
 * Fetch all students accessible to staff.
 */
export async function getStudents(): Promise<StudentProfile[]> {
  const response = await apiClient.get<StudentProfile[]>("/api/v1/students/");
  return response.data;
}

/**
 * Fetch the authenticated student's own profile via GET /api/v1/students/me.
 */
export async function getStudentProfileMe(): Promise<StudentProfile> {
  const response = await apiClient.get<StudentProfile>("/api/v1/students/me");
  return response.data;
}

/**
 * Resolve the authenticated student's profile via GET /api/v1/students/me.
 */
export async function getCurrentStudentProfile(
  _userId?: number,
  _email?: string
): Promise<StudentProfile | null> {
  try {
    const response = await apiClient.get<StudentProfile>("/api/v1/students/me");
    return response.data;
  } catch {
    return null;
  }
}

/**
 * Fetch a single student record by ID.
 */
export async function getStudentById(studentId: number): Promise<StudentProfile> {
  const response = await apiClient.get<StudentProfile>(`/api/v1/students/${studentId}`);
  return response.data;
}

/**
 * Fetch course details by ID.
 */
export async function getCourseById(courseId: number): Promise<CourseInfo | null> {
  try {
    const response = await apiClient.get<CourseInfo>(`/api/v1/courses/${courseId}`);
    return response.data;
  } catch {
    return null;
  }
}

/**
 * Fetch department details by ID.
 */
export async function getDepartmentById(departmentId: number): Promise<DepartmentInfo | null> {
  try {
    const response = await apiClient.get<DepartmentInfo>(`/api/v1/departments/${departmentId}`);
    return response.data;
  } catch {
    return null;
  }
}

/**
 * Fetch academic results for a student in a specific semester.
 */
export async function getStudentSemesterResult(
  studentId: number,
  semester: number
): Promise<StudentSemesterResultResponse | null> {
  try {
    const response = await apiClient.get<StudentSemesterResultResponse>(
      `/api/v1/results/student/${studentId}/semester/${semester}`
    );
    return response.data;
  } catch {
    return null;
  }
}

/**
 * Fetch overall academic summary across all enrollments.
 */
export async function getStudentAcademicSummary(
  studentId: number
): Promise<StudentAcademicSummaryResponse | null> {
  try {
    const response = await apiClient.get<StudentAcademicSummaryResponse>(
      `/api/v1/results/student/${studentId}/summary`
    );
    return response.data;
  } catch {
    return null;
  }
}

/**
 * Fetch performance and attendance profile for a specific enrollment.
 */
export async function getEnrollmentPerformanceProfile(
  enrollmentId: number
): Promise<EnrollmentPerformanceProfileResponse | null> {
  try {
    const response = await apiClient.get<EnrollmentPerformanceProfileResponse>(
      `/api/v1/results/enrollment/${enrollmentId}/performance`
    );
    return response.data;
  } catch {
    return null;
  }
}
