import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import type { UserRole } from "./authTypes";

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
  children?: React.ReactNode;
}

export const getRoleHomePath = (role?: UserRole): string => {
  switch (role) {
    case "student":
      return "/student";
    case "faculty":
      return "/faculty";
    case "hod":
      return "/hod";
    case "admin":
      return "/admin";
    default:
      return "/login";
  }
};

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  allowedRoles,
  children,
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "100vh",
          fontFamily: "system-ui, -apple-system, sans-serif",
          color: "#4a5568",
        }}
      >
        <p>Verifying session...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // If authenticated user lacks the required role, redirect to their own role landing page
    return <Navigate to={getRoleHomePath(user.role)} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;
