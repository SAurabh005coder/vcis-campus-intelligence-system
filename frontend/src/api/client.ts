import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

export const TOKEN_STORAGE_KEY = "vcis_auth_token";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach Authorization Bearer token to authenticated requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Catch 401 Unauthorized responses to clear stale credentials
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      window.dispatchEvent(new Event("vcis:unauthorized"));
    }
    return Promise.reject(error);
  }
);

export default apiClient;