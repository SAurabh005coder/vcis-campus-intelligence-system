import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../../auth/AuthContext";
import {
  type AdminProfile,
  type CreateUserRequest,
  type SubjectInfo,
  type UpdateInterventionRequest,
  type UserResponse,
  createUserAccount,
  getAdminProfile,
  getStudentPredictionForAdmin,
  getSystemCourses,
  getSystemDepartments,
  getSystemFaculty,
  getSystemInterventions,
  getSystemStudents,
  getSystemSubjects,
  getSystemUsers,
  updateSystemIntervention,
} from "../../api/adminApi";
import type { DepartmentInfo, CourseInfo, StudentProfile } from "../../api/studentApi";
import type { FacultyProfile } from "../../api/facultyApi";
import type { InterventionResponse } from "../../api/interventionApi";
import type { PredictionResponse } from "../../api/predictionApi";

import { AdminOverview } from "../../components/admin/AdminOverview";
import { AcademicStructureOverview } from "../../components/admin/AcademicStructureOverview";
import { AdminInterventionOverview } from "../../components/admin/AdminInterventionOverview";
import { AdminUserDirectory } from "../../components/admin/AdminUserDirectory";
import { AdminStudentDirectory } from "../../components/admin/AdminStudentDirectory";
import { AdminFacultyDirectory } from "../../components/admin/AdminFacultyDirectory";
import { AdminStudentReview } from "../../components/admin/AdminStudentReview";
import { UserProvisionModal } from "../../components/admin/UserProvisionModal";
import { AdminProposalManagement } from "../../components/admin/AdminProposalManagement";

type AdminTab = "overview" | "proposals" | "users" | "students" | "faculty" | "interventions";

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();

  // Navigation state
  const [activeTab, setActiveTab] = useState<AdminTab>("overview");

  // Core metadata states
  const [admin, setAdmin] = useState<AdminProfile | null>(null);
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [departments, setDepartments] = useState<DepartmentInfo[]>([]);
  const [courses, setCourses] = useState<CourseInfo[]>([]);
  const [subjects, setSubjects] = useState<SubjectInfo[]>([]);
  const [faculty, setFaculty] = useState<FacultyProfile[]>([]);
  const [students, setStudents] = useState<StudentProfile[]>([]);
  const [interventions, setInterventions] = useState<InterventionResponse[]>([]);

  // Selection & Inspection states
  const [selectedStudent, setSelectedStudent] = useState<StudentProfile | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [isPredictionLoading, setIsPredictionLoading] = useState(false);
  const [insufficientData, setInsufficientData] = useState(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);

  // User Provisioning modal
  const [isProvisionModalOpen, setIsProvisionModalOpen] = useState(false);
  const [isSubmittingUser, setIsSubmittingUser] = useState(false);

  // Loading & Feedback
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load institutional datasets
  const loadInitialData = useCallback(async () => {
    if (!user) return;
    setIsDataLoading(true);
    setErrorMessage(null);

    try {
      const [
        adminData,
        usersData,
        deptsData,
        coursesData,
        subjectsData,
        facultyData,
        studentsData,
        interventionsData,
      ] = await Promise.all([
        getAdminProfile(user.id, user.email),
        getSystemUsers().catch(() => []),
        getSystemDepartments().catch(() => []),
        getSystemCourses().catch(() => []),
        getSystemSubjects().catch(() => []),
        getSystemFaculty().catch(() => []),
        getSystemStudents().catch(() => []),
        getSystemInterventions().catch(() => []),
      ]);

      setAdmin(adminData);
      setUsers(usersData);
      setDepartments(deptsData);
      setCourses(coursesData);
      setSubjects(subjectsData);
      setFaculty(facultyData);
      setStudents(studentsData);
      setInterventions(interventionsData);
    } catch {
      setErrorMessage("Failed to load institutional datasets.");
    } finally {
      setIsDataLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Reset student inspection state when selected student changes
  useEffect(() => {
    setPrediction(null);
    setPredictionError(null);
    setInsufficientData(false);
  }, [selectedStudent]);

  // Selected student's department and course
  const selectedStudentDept = useMemo(() => {
    if (!selectedStudent) return null;
    return departments.find((d) => d.id === selectedStudent.department_id) || null;
  }, [departments, selectedStudent]);

  const selectedStudentCourse = useMemo(() => {
    if (!selectedStudent) return null;
    return courses.find((c) => c.id === selectedStudent.course_id) || null;
  }, [courses, selectedStudent]);

  // Selected student's interventions
  const selectedStudentInterventions = useMemo(() => {
    if (!selectedStudent) return [];
    return interventions.filter((i) => i.student_id === selectedStudent.id);
  }, [interventions, selectedStudent]);

  // On-demand ML Prediction evaluation
  const handleGeneratePrediction = async () => {
    if (!selectedStudent) return;
    setIsPredictionLoading(true);
    setPredictionError(null);
    setInsufficientData(false);

    try {
      const res = await getStudentPredictionForAdmin(
        selectedStudent.id,
        selectedStudent.current_semester
      );

      setPrediction(res.data);
      setInsufficientData(res.insufficientData);
      setPredictionError(res.errorMessage);
    } catch {
      setPredictionError("Failed to communicate with prediction service.");
    } finally {
      setIsPredictionLoading(false);
    }
  };

  // Provision new user
  const handleCreateUser = async (payload: CreateUserRequest) => {
    setIsSubmittingUser(true);
    setErrorMessage(null);

    try {
      const newUser = await createUserAccount(payload);
      setUsers((prev) => [newUser, ...prev]);
      setSuccessMessage(
        `User account '${newUser.email}' (${newUser.role.toUpperCase()}) successfully registered with ID #${newUser.id}.`
      );
      setTimeout(() => setSuccessMessage(null), 5000);
      setIsProvisionModalOpen(false);
    } catch (err: unknown) {
      if (err instanceof Error) {
        throw err;
      } else {
        throw new Error("Failed to provision user account.");
      }
    } finally {
      setIsSubmittingUser(false);
    }
  };

  // Update intervention lifecycle (status, action plan, follow up)
  const handleUpdateIntervention = async (id: number, payload: UpdateInterventionRequest) => {
    try {
      const updated = await updateSystemIntervention(id, payload);
      setInterventions((prev) => prev.map((i) => (i.id === id ? updated : i)));
      setSuccessMessage(`Intervention record #${id} updated successfully.`);
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to update intervention record.");
      }
      setTimeout(() => setErrorMessage(null), 5000);
      throw err;
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div className="vcis-page-header" style={{ marginBottom: "var(--space-6)" }}>
        <div>
          <h1 className="vcis-page-title">Institutional Administration</h1>
          <p className="vcis-page-subtitle">
            Manage academic structure, users, students, faculty, and intervention operations across VCIS.
          </p>
        </div>
        <div className="vcis-page-actions">
          <button
            id="refresh-admin-data-btn"
            onClick={loadInitialData}
            disabled={isDataLoading}
            className="vcis-btn vcis-btn-secondary"
          >
            {isDataLoading ? "Refreshing..." : "Refresh Data"}
          </button>
        </div>
      </div>

      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        {/* Success Banner */}
        {successMessage && (
          <div className="vcis-alert vcis-alert-success" style={{ marginBottom: "var(--space-4)" }}>
            ✓ {successMessage}
          </div>
        )}

        {/* Global Error Banner */}
        {errorMessage && (
          <div className="vcis-alert vcis-alert-danger" style={{ marginBottom: "var(--space-4)" }}>
            ✕ {errorMessage}
          </div>
        )}

        {/* Admin Overview & System Metrics Card */}
        <AdminOverview
          admin={admin}
          totalUsers={users.length}
          totalStudents={students.length}
          totalFaculty={faculty.length}
          totalDepartments={departments.length}
          totalCourses={courses.length}
          totalSubjects={subjects.length}
          totalInterventions={interventions.length}
          onOpenProvisionModal={() => setIsProvisionModalOpen(true)}
        />

        {/* Tab Navigation Controls */}
        <div className="vcis-tab-list" role="tablist" style={{ marginBottom: "var(--space-6)" }}>
          {[
            { id: "overview", label: "Overview & Structure" },
            { id: "proposals", label: "Academic Proposals" },
            { id: "users", label: `User Accounts (${users.length})` },
            { id: "students", label: `Students (${students.length})` },
            { id: "faculty", label: `Faculty (${faculty.length})` },
            { id: "interventions", label: `Interventions (${interventions.length})` },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                role="tab"
                aria-selected={isActive}
                onClick={() => setActiveTab(tab.id as AdminTab)}
                className={`vcis-tab-btn ${isActive ? "is-active" : ""}`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab 1: Overview & Academic Structure Hierarchy */}
        {activeTab === "overview" && (
          <div>
            <AcademicStructureOverview
              departments={departments}
              courses={courses}
              subjects={subjects}
              students={students}
              faculty={faculty}
            />
          </div>
        )}

        {/* Tab: Academic Proposals Dedicated View */}
        {activeTab === "proposals" && (
          <div>
            <AdminProposalManagement
              departments={departments}
              courses={courses}
              onProposalApproved={() => loadInitialData()}
            />
          </div>
        )}

        {/* Tab 2: User Accounts Directory */}
        {activeTab === "users" && (
          <div>
            <AdminUserDirectory
              users={users}
              isLoading={isDataLoading}
              onOpenProvisionModal={() => setIsProvisionModalOpen(true)}
            />
          </div>
        )}

        {/* Tab 3: Students Directory & Deep Inspection */}
        {activeTab === "students" && (
          <div>
            {selectedStudent && (
              <AdminStudentReview
                student={selectedStudent}
                department={selectedStudentDept}
                course={selectedStudentCourse}
                prediction={prediction}
                isPredictionLoading={isPredictionLoading}
                insufficientData={insufficientData}
                predictionError={predictionError}
                onGeneratePrediction={handleGeneratePrediction}
                interventions={selectedStudentInterventions}
                isInterventionsLoading={false}
                onClose={() => setSelectedStudent(null)}
              />
            )}

            <AdminStudentDirectory
              students={students}
              departments={departments}
              courses={courses}
              selectedStudent={selectedStudent}
              onSelectStudent={(s) => setSelectedStudent(s)}
              isLoading={isDataLoading}
            />
          </div>
        )}

        {/* Tab 4: Faculty Directory */}
        {activeTab === "faculty" && (
          <div>
            <AdminFacultyDirectory
              faculty={faculty}
              departments={departments}
              isLoading={isDataLoading}
            />
          </div>
        )}

        {/* Tab 5: Institutional Interventions Oversight */}
        {activeTab === "interventions" && (
          <div>
            <AdminInterventionOverview
              interventions={interventions}
              students={students}
              faculty={faculty}
              onUpdateIntervention={handleUpdateIntervention}
              isLoading={isDataLoading}
            />
          </div>
        )}

        {/* User Provisioning Modal */}
        <UserProvisionModal
          isOpen={isProvisionModalOpen}
          onClose={() => setIsProvisionModalOpen(false)}
          onSubmit={handleCreateUser}
          isSubmitting={isSubmittingUser}
        />
      </div>
    </div>
  );
};

export default AdminDashboard;
