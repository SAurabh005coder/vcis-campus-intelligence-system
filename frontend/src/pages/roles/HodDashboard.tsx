import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../../auth/AuthContext";
import {
  type HodProfile,
  createHodIntervention,
  getCourses,
  getCurrentHodProfile,
  getDepartments,
  getFacultyList,
  getInterventions,
  getStudentPredictionForHod,
  getStudents,
  updateHodIntervention,
} from "../../api/hodApi";
import type { DepartmentInfo, CourseInfo, StudentProfile } from "../../api/studentApi";
import type { PredictionResponse, AcademicStatus } from "../../api/predictionApi";
import type { InterventionResponse } from "../../api/interventionApi";
import type {
  CreateInterventionRequest,
  FacultyProfile,
  UpdateInterventionRequest,
} from "../../api/facultyApi";

import { HodOverview } from "../../components/hod/HodOverview";
import { DepartmentOverview } from "../../components/hod/DepartmentOverview";
import { HodInterventionOverview } from "../../components/hod/HodInterventionOverview";
import { PredictionStatusOverview } from "../../components/hod/PredictionStatusOverview";
import { HodStudentTable } from "../../components/hod/HodStudentTable";
import { HodStudentReview } from "../../components/hod/HodStudentReview";
import { HodInterventionModal } from "../../components/hod/HodInterventionModal";

export const HodDashboard: React.FC = () => {
  const { user } = useAuth();

  // Core metadata states
  const [hod, setHod] = useState<HodProfile | null>(null);
  const [departments, setDepartments] = useState<DepartmentInfo[]>([]);
  const [courses, setCourses] = useState<CourseInfo[]>([]);
  const [facultyList, setFacultyList] = useState<FacultyProfile[]>([]);
  const [departmentInfo, setDepartmentInfo] = useState<DepartmentInfo | null>(null);
  const [departmentError, setDepartmentError] = useState<string | null>(null);

  // Roster and intervention datasets (backend department-scoped for HOD)
  const [students, setStudents] = useState<StudentProfile[]>([]);
  const [interventions, setInterventions] = useState<InterventionResponse[]>([]);

  // Selection & Prediction states
  const [selectedStudent, setSelectedStudent] = useState<StudentProfile | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [isPredictionLoading, setIsPredictionLoading] = useState(false);
  const [insufficientData, setInsufficientData] = useState(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);

  // Map of on-demand student evaluations run during this session
  const [sessionEvaluations, setSessionEvaluations] = useState<
    Map<number, { score: number; status: AcademicStatus }>
  >(new Map());

  // Loading and feedback states
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [isInterventionsLoading, setIsInterventionsLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmittingModal, setIsSubmittingModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load initial HOD and department-scoped datasets
  const loadInitialData = useCallback(async () => {
    if (!user) return;
    setIsDataLoading(true);
    setErrorMessage(null);
    setDepartmentError(null);

    try {
      // 1. Establish HOD profile and authoritative department scope first
      const hodData = await getCurrentHodProfile(user.id, user.email);
      setHod(hodData);

      if (!hodData || !hodData.department_id) {
        setDepartmentError(
          "Your HOD account is not currently linked to an academic department in the faculty registry. Please contact the system administrator to assign your faculty profile to a department."
        );
        setIsDataLoading(false);
        return;
      }

      // 2. Fetch department-scoped datasets and relevant institutional metadata
      const [deptsData, coursesData, facultyData, studentsData, interventionsData] =
        await Promise.all([
          getDepartments().catch(() => []),
          getCourses().catch(() => []),
          getFacultyList().catch(() => []),
          getStudents().catch(() => []),
          getInterventions().catch(() => []),
        ]);

      setDepartments(deptsData);
      setCourses(coursesData);
      setFacultyList(facultyData);
      setStudents(studentsData);
      setInterventions(interventionsData);

      const assignedDept =
        deptsData.find((d) => d.id === hodData.department_id) || null;
      setDepartmentInfo(assignedDept);

      // Pre-select first student if available from department roster
      if (studentsData.length > 0) {
        setSelectedStudent(studentsData[0]);
      } else {
        setSelectedStudent(null);
      }
    } catch {
      setErrorMessage("Failed to load initial institutional oversight data.");
    } finally {
      setIsDataLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Adjust selected student when student list changes
  useEffect(() => {
    if (!selectedStudent && students.length > 0) {
      setSelectedStudent(students[0]);
    } else if (
      selectedStudent &&
      !students.some((s) => s.id === selectedStudent.id)
    ) {
      setSelectedStudent(students.length > 0 ? students[0] : null);
    }
  }, [students, selectedStudent]);

  // Reset student review state when selected student changes
  useEffect(() => {
    setPrediction(null);
    setPredictionError(null);
    setInsufficientData(false);
  }, [selectedStudent]);

  // Interventions for currently selected student
  const studentInterventions = useMemo(() => {
    if (!selectedStudent) return [];
    return interventions.filter((i) => i.student_id === selectedStudent.id);
  }, [interventions, selectedStudent]);

  // Selected student's department info
  const selectedStudentDept = useMemo(() => {
    if (!selectedStudent) return null;
    return departments.find((d) => d.id === selectedStudent.department_id) || null;
  }, [departments, selectedStudent]);

  // Explicit Action: On-demand ML Prediction for selected student
  const handleGeneratePrediction = async () => {
    if (!selectedStudent) return;
    setIsPredictionLoading(true);
    setPredictionError(null);
    setInsufficientData(false);

    try {
      const res = await getStudentPredictionForHod(
        selectedStudent.id,
        selectedStudent.current_semester
      );

      setPrediction(res.data);
      setInsufficientData(res.insufficientData);
      setPredictionError(res.errorMessage);

      if (res.data) {
        setSessionEvaluations((prev) => {
          const updated = new Map(prev);
          updated.set(selectedStudent.id, {
            score: res.data!.predicted_final_semester_score,
            status: res.data!.academic_status,
          });
          return updated;
        });
      }
    } catch {
      setPredictionError("Failed to communicate with the ML prediction service.");
    } finally {
      setIsPredictionLoading(false);
    }
  };

  // Explicit Action: Create Academic Intervention
  const handleCreateIntervention = async (payload: CreateInterventionRequest) => {
    setIsSubmittingModal(true);
    setErrorMessage(null);
    try {
      await createHodIntervention(payload);
      setSuccessMessage("Academic intervention successfully created and recorded.");
      setTimeout(() => setSuccessMessage(null), 4000);
      setIsModalOpen(false);

      // Refresh interventions dataset
      setIsInterventionsLoading(true);
      const refreshed = await getInterventions();
      setInterventions(refreshed);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to create academic intervention.");
      }
    } finally {
      setIsSubmittingModal(false);
      setIsInterventionsLoading(false);
    }
  };

  // Explicit Action: Update Intervention Workflow Status
  const handleUpdateIntervention = async (
    id: number,
    payload: UpdateInterventionRequest
  ) => {
    try {
      await updateHodIntervention(id, payload);
      setSuccessMessage("Intervention workflow status updated.");
      setTimeout(() => setSuccessMessage(null), 4000);

      // Refresh interventions list
      const refreshed = await getInterventions();
      setInterventions(refreshed);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to update intervention workflow.");
      }
    }
  };

  return (
    <div>
      {/* Workspace Header with Refresh Data Action */}
      <div className="vcis-page-header" style={{ marginBottom: "var(--space-6)" }}>
        <div>
          <h1 className="vcis-page-title">Department Intelligence</h1>
          <p className="vcis-page-subtitle">
            Monitor academic performance, identify students requiring attention, and oversee interventions across your department.
          </p>
        </div>
        <div className="vcis-page-actions">
          <button
            id="refresh-hod-data-btn"
            onClick={loadInitialData}
            disabled={isDataLoading}
            className="vcis-btn vcis-btn-secondary"
          >
            {isDataLoading ? "Refreshing..." : "Refresh Data"}
          </button>
        </div>
      </div>

      <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
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

        {/* Unassigned Department Error Banner */}
        {departmentError && (
          <div className="vcis-alert vcis-alert-warning" style={{ marginBottom: "var(--space-6)" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "var(--space-3)" }}>
              <span style={{ fontSize: "1.25rem", lineHeight: 1 }}>⚠️</span>
              <div>
                <h4 style={{ margin: "0 0 var(--space-1) 0", fontSize: "var(--vcis-font-size-sm)", fontWeight: "var(--vcis-font-weight-bold)" }}>
                  Department Oversight Scope Unassigned
                </h4>
                <p style={{ margin: 0, fontSize: "var(--vcis-font-size-xs)", lineHeight: 1.5 }}>
                  {departmentError}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* HOD Header and Fixed Scope Indicator */}
        <HodOverview
          hod={hod}
          departmentName={
            departmentInfo?.name ||
            (hod?.department_id
              ? `Department #${hod.department_id}`
              : "Unassigned")
          }
          departmentCode={departmentInfo?.code}
          totalStudentsCount={students.length}
          totalInterventionsCount={interventions.length}
        />

        {!departmentError && (
          <>
            {/* Department Roster and Semester Breakdown */}
            {hod?.department_id && (
              <DepartmentOverview
                students={students}
                courses={courses}
                departmentId={hod.department_id}
              />
            )}

            {/* Department Analytics Row: Status Distribution & Intervention Oversight */}
            <div className="vcis-hod-analytics-grid">
              <PredictionStatusOverview
                interventions={interventions}
                sessionEvaluations={sessionEvaluations}
              />
              <HodInterventionOverview interventions={interventions} />
            </div>

            {/* Student Attention Table */}
            <HodStudentTable
              students={students}
              departments={departments}
              interventions={interventions}
              selectedStudent={selectedStudent}
              onSelectStudent={(s) => setSelectedStudent(s)}
              isLoading={isDataLoading}
            />

            {/* Selected Student Deep Review */}
            {selectedStudent ? (
              <HodStudentReview
                student={selectedStudent}
                department={selectedStudentDept}
                prediction={prediction}
                isPredictionLoading={isPredictionLoading}
                insufficientData={insufficientData}
                predictionError={predictionError}
                onGeneratePrediction={handleGeneratePrediction}
                interventions={studentInterventions}
                isInterventionsLoading={isInterventionsLoading}
                onUpdateIntervention={handleUpdateIntervention}
                onOpenInterventionModal={() => setIsModalOpen(true)}
              />
            ) : (
              <div className="vcis-empty-state" style={{ padding: "var(--space-8)" }}>
                <p className="vcis-empty-title">No Student Selected</p>
                <p className="vcis-empty-text">
                  Select a student from the department roster above to inspect academic indicators, run on-demand early predictions, and oversee interventions.
                </p>
              </div>
            )}

            {/* Intervention Creation Modal */}
            {isModalOpen && selectedStudent && prediction && (
              <HodInterventionModal
                student={selectedStudent}
                defaultFacultyId={hod?.faculty_id || null}
                facultyList={facultyList}
                prediction={prediction}
                onSubmit={handleCreateIntervention}
                onClose={() => setIsModalOpen(false)}
                isSubmitting={isSubmittingModal}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default HodDashboard;
