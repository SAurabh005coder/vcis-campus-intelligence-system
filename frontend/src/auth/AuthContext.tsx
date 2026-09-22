import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import apiClient, { TOKEN_STORAGE_KEY } from "../api/client";
import type {
  AuthContextValue,
  LoginRequest,
  LoginResponse,
  User,
} from "./authTypes";

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_STORAGE_KEY)
  );
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  // Initialize and verify persisted session
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await apiClient.get<User>("/api/v1/users/me", {
          headers: {
            Authorization: `Bearer ${storedToken}`,
          },
        });
        setUser(response.data);
        setToken(storedToken);
      } catch {
        // Token is invalid or expired
        logout();
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    // Listen for unauthorized events emitted by Axios response interceptor
    const handleUnauthorized = () => {
      logout();
    };

    window.addEventListener("vcis:unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("vcis:unauthorized", handleUnauthorized);
    };
  }, [logout]);

  const login = async (credentials: LoginRequest): Promise<User> => {
    // 1. Authenticate credentials against backend endpoint
    const loginRes = await apiClient.post<LoginResponse>(
      "/api/v1/auth/login",
      credentials
    );

    const accessToken = loginRes.data.access_token;
    localStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
    setToken(accessToken);

    // 2. Fetch authenticated user profile using newly obtained token
    const userRes = await apiClient.get<User>("/api/v1/users/me", {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const authenticatedUser = userRes.data;
    setUser(authenticatedUser);
    return authenticatedUser;
  };

  const value: AuthContextValue = {
    isAuthenticated: !!token && !!user,
    isLoading,
    user,
    token,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
