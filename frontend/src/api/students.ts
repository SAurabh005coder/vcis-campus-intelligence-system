import apiClient from "./client";

export interface Student {
  id: number;
  name: string;
  email: string;
}

export async function getStudents(): Promise<Student[]> {
  const response = await apiClient.get<Student[]>("/api/v1/students/");
  return response.data;
}

export async function getStudent(
  studentId: number
): Promise<Student> {
  const response = await apiClient.get<Student>(
    `/api/v1/students/${studentId}`
  );

  return response.data;
}

export async function createStudent(
  name: string,
  email: string
): Promise<Student> {
  const response = await apiClient.post<Student>("/api/v1/students/", {
    name,
    email,
  });

  return response.data;
}

export async function updateStudent(
  studentId: number,
  name: string,
  email: string
): Promise<Student> {
  const response = await apiClient.put<Student>(
    `/api/v1/students/${studentId}`,
    {
      name,
      email,
    }
  );

  return response.data;
}



export async function deleteStudent(
  studentId: number
): Promise<void> {
  await apiClient.delete(`/api/v1/students/${studentId}`);
}