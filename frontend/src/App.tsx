import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import { AuthProvider, useAuth } from "./auth/AuthContext";
import { ProtectedRoute, getRoleHomePath } from "./auth/ProtectedRoute";
import { Login } from "./pages/Login";
import { StudentDashboard } from "./pages/roles/StudentDashboard";
import { FacultyDashboard } from "./pages/roles/FacultyDashboard";
import { HodDashboard } from "./pages/roles/HodDashboard";
import { AdminDashboard } from "./pages/roles/AdminDashboard";
import { AppLayout } from "./layouts/AppLayout";

function RootRedirect() {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "100vh",
          fontFamily: "system-ui, sans-serif",
          color: "#4a5568",
        }}
      >
        Initializing session...
      </div>
    );
  }

  if (isAuthenticated && user) {
    return <Navigate to={getRoleHomePath(user.role)} replace />;
  }

  return <Navigate to="/login" replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      {/* Public Login Route */}
      <Route path="/login" element={<Login />} />

      {/* Root redirect based on auth & role */}
      <Route path="/" element={<RootRedirect />} />

      {/* Protected Authenticated Routes Wrapped in VCIS Shared Shell */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route
          path="/student"
          element={
            <ProtectedRoute allowedRoles={["student"]}>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/faculty"
          element={
            <ProtectedRoute allowedRoles={["faculty"]}>
              <FacultyDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/hod"
          element={
            <ProtectedRoute allowedRoles={["hod"]}>
              <HodDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Safe redirect for obsolete /students route to authenticated role dashboard */}
      <Route path="/students" element={<Navigate to="/" replace />} />

      {/* Fallback to root redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;