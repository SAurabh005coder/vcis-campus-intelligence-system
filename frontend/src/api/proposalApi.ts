import apiClient from "./client";

export type ProposalStatus = "DRAFT" | "PENDING_APPROVAL" | "APPROVED" | "REJECTED";

export interface CourseProposal {
  id: number;
  department_id: number;
  proposed_by: number;
  name: string;
  code: string;
  description: string | null;
  duration_years: number;
  total_semesters: number;
  status: ProposalStatus;
  reviewed_by: number | null;
  reviewed_at: string | null;
  review_comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubjectProposal {
  id: number;
  course_id: number;
  proposed_by: number;
  name: string;
  code: string;
  semester: number;
  credits: number;
  description: string | null;
  status: ProposalStatus;
  reviewed_by: number | null;
  reviewed_at: string | null;
  review_comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateCourseProposalPayload {
  name: string;
  code: string;
  description?: string | null;
  duration_years: number;
  total_semesters: number;
}

export interface CreateSubjectProposalPayload {
  course_id: number;
  name: string;
  code: string;
  semester: number;
  credits: number;
  description?: string | null;
}

export interface ReviewProposalPayload {
  review_comment?: string | null;
}

// Course Proposal APIs
export async function getCourseProposals(): Promise<CourseProposal[]> {
  const response = await apiClient.get<CourseProposal[]>("/api/v1/course-proposals/");
  return response.data;
}

export async function getCourseProposal(id: number): Promise<CourseProposal> {
  const response = await apiClient.get<CourseProposal>(`/api/v1/course-proposals/${id}`);
  return response.data;
}

export async function createCourseProposal(data: CreateCourseProposalPayload): Promise<CourseProposal> {
  const response = await apiClient.post<CourseProposal>("/api/v1/course-proposals/", data);
  return response.data;
}

export async function approveCourseProposal(id: number, comment?: string): Promise<CourseProposal> {
  const response = await apiClient.post<CourseProposal>(`/api/v1/course-proposals/${id}/approve`, {
    review_comment: comment || null,
  });
  return response.data;
}

export async function rejectCourseProposal(id: number, comment: string): Promise<CourseProposal> {
  const response = await apiClient.post<CourseProposal>(`/api/v1/course-proposals/${id}/reject`, {
    review_comment: comment,
  });
  return response.data;
}

// Subject Proposal APIs
export async function getSubjectProposals(): Promise<SubjectProposal[]> {
  const response = await apiClient.get<SubjectProposal[]>("/api/v1/subject-proposals/");
  return response.data;
}

export async function getSubjectProposal(id: number): Promise<SubjectProposal> {
  const response = await apiClient.get<SubjectProposal>(`/api/v1/subject-proposals/${id}`);
  return response.data;
}

export async function createSubjectProposal(data: CreateSubjectProposalPayload): Promise<SubjectProposal> {
  const response = await apiClient.post<SubjectProposal>("/api/v1/subject-proposals/", data);
  return response.data;
}

export async function approveSubjectProposal(id: number, comment?: string): Promise<SubjectProposal> {
  const response = await apiClient.post<SubjectProposal>(`/api/v1/subject-proposals/${id}/approve`, {
    review_comment: comment || null,
  });
  return response.data;
}

export async function rejectSubjectProposal(id: number, comment: string): Promise<SubjectProposal> {
  const response = await apiClient.post<SubjectProposal>(`/api/v1/subject-proposals/${id}/reject`, {
    review_comment: comment,
  });
  return response.data;
}
