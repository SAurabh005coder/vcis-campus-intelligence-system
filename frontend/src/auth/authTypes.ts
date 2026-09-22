/**
 * VCIS 3.0 — Authentication and Role Types
 * Matches the backend user and authentication schemas exactly.
 */

export type UserRole = "student" | "faculty" | "hod" | "admin";

export interface User {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  token: string | null;
}

export interface AuthContextValue extends AuthState {
  login: (credentials: LoginRequest) => Promise<User>;
  logout: () => void;
}
