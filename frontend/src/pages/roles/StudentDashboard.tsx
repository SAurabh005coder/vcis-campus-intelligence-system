import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "../../auth/AuthContext";
import {
  type CourseInfo,
  type DepartmentInfo,
  type EnrollmentPerformanceProfileResponse,
  type StudentAcademicSummaryResponse,
  type StudentProfile,
  getCourseById,
  getCurrentStudentProfile,
  getDepartmentById,
  getEnrollmentPerformanceProfile,
  getStudentAcademicSummary,
} from "../../api/studentApi";
import {
  type PredictionResponse,
  getStudentPrediction,
} from "../../api/predictionApi";
import {
  type InterventionResponse,
  getMyInterventions,
} from "../../api/interventionApi";

import { AcademicOverview } from "../../components/student/AcademicOverview";
import { AttendanceOverview } from "../../components/student/AttendanceOverview";
import { AssessmentResultSection } from "../../components/student/AssessmentResultSection";
import { SemesterHistory } from "../../components/student/SemesterHistory";
import { PredictionCard } from "../../components/student/PredictionCard";
import { AcademicKpiGrid } from "../../components/student/AcademicKpiGrid";
import { InterventionList } from "../../components/student/InterventionList";

export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();

  // State: Student Identity & Academic Profile
  const [student, setStudent] = useState<StudentProfile | null>(null);
  const [course, setCourse] = useState<CourseInfo | null>(null);
  const [department, setDepartment] = useState<DepartmentInfo | null>(null);
  const [isProfileLoading, setIsProfileLoading] = useState<boolean>(true);
  const [profileError, setProfileError] = useState<string | null>(null);

  // State: Dynamic Academic Performance & Results
  const [academicSummary, setAcademicSummary] = useState<StudentAcademicSummaryResponse | null>(null);
  const [performanceProfiles, setPerformanceProfiles] = useState<EnrollmentPerformanceProfileResponse[]>([]);
  const [isResultsLoading, setIsResultsLoading] = useState<boolean>(true);

  // State: Early Prediction
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [isPredictionLoading, setIsPredictionLoading] = useState<boolean>(true);
  const [insufficientData, setInsufficientData] = useState<boolean>(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);

  // State: Interventions
  const [interventions, setInterventions] = useState<InterventionResponse[]>([]);
  const [isInterventionsLoading, setIsInterventionsLoading] = useState<boolean>(true);
  const [interventionsError, setInterventionsError] = useState<string | null>(null);

  const fetchPrediction = useCallback(async (studentId: number, currentSem: number) => {
    setIsPredictionLoading(true);
    setPredictionError(null);
    setInsufficientData(false);

    try {
      const predResult = await getStudentPrediction(studentId, currentSem);
      setPrediction(predResult.data);
      setInsufficientData(predResult.insufficientData);
      setPredictionError(predResult.errorMessage);
    } catch {
      setPredictionError("Could not complete early prediction evaluation.");
    } finally {
      setIsPredictionLoading(false);
    }
  }, []);

  const loadDashboardData = useCallback(async () => {
    if (!user) return;

    setIsProfileLoading(true);
    setProfileError(null);

    try {
      // 1. Resolve Student Profile via dedicated secure /api/v1/students/me endpoint
      const studentProfile = await getCurrentStudentProfile(user.id, user.email);

      if (!studentProfile) {
        setProfileError(
          "Student academic profile not found. Please verify your enrollment status with the academic administration."
        );
        setIsProfileLoading(false);
        setIsResultsLoading(false);
        setIsPredictionLoading(false);
        setIsInterventionsLoading(false);
        return;
      }

      setStudent(studentProfile);
      setIsProfileLoading(false);

      // 2. Fetch Course & Department metadata in background
      getCourseById(studentProfile.course_id).then(setCourse).catch(() => null);
      getDepartmentById(studentProfile.department_id).then(setDepartment).catch(() => null);

      // 3. Fetch Dynamic Academic Results & Subject Performance Profiles
      setIsResultsLoading(true);
      getStudentAcademicSummary(studentProfile.id)
        .then(async (summary) => {
          setAcademicSummary(summary);
          if (summary && summary.subjects && summary.subjects.length > 0) {
            const profiles = await Promise.all(
              summary.subjects.map((sub) =>
                getEnrollmentPerformanceProfile(sub.enrollment_id).catch(() => null)
              )
            );
            setPerformanceProfiles(
              profiles.filter((p): p is EnrollmentPerformanceProfileResponse => p !== null)
            );
          } else {
            setPerformanceProfiles([]);
          }
        })
        .catch(() => {
          setAcademicSummary(null);
          setPerformanceProfiles([]);
        })
        .finally(() => {
          setIsResultsLoading(false);
        });

      // 4. Fetch Early Prediction for Student's Current Semester
      fetchPrediction(studentProfile.id, studentProfile.current_semester);

      // 5. Fetch Interventions (automatically scoped to this student by backend)
      setIsInterventionsLoading(true);
      setInterventionsError(null);

      getMyInterventions()
        .then((data) => {
          setInterventions(data);
        })
        .catch((err) => {
          const detail =
            err?.response?.data?.detail || "Could not retrieve intervention records.";
          setInterventionsError(detail);
        })
        .finally(() => {
          setIsInterventionsLoading(false);
        });
    } catch {
      setProfileError("An unexpected error occurred while loading your academic profile.");
      setIsProfileLoading(false);
      setIsResultsLoading(false);
      setIsPredictionLoading(false);
      setIsInterventionsLoading(false);
    }
  }, [user, fetchPrediction]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  return (
    <div>
      {/* Page Header with Institutional Title and Action Slot */}
      <div className="vcis-page-header" style={{ marginBottom: "1.5rem" }}>
        <div>
          <h1 className="vcis-page-title">Student Portal</h1>
          <p className="vcis-page-subtitle">
            Academic performance, attendance records, and early predictive intelligence.
          </p>
        </div>
        <div>
          <button
            onClick={loadDashboardData}
            className="vcis-button vcis-button-secondary vcis-button-sm"
            title="Reload academic overview and predictions"
          >
            Refresh Data
          </button>
        </div>
      </div>

      <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
        {/* Profile Level Loading / Error */}
        {isProfileLoading ? (
          <div
            className="vcis-card"
            style={{
              padding: "var(--vcis-space-8)",
              textAlign: "center",
              color: "var(--vcis-text-muted)",
            }}
          >
            <div style={{ fontSize: "var(--vcis-text-base)", fontWeight: "var(--vcis-font-medium)" }}>
              Loading your academic profile...
            </div>
          </div>
        ) : profileError ? (
          <div
            className="vcis-card"
            style={{
              padding: "var(--vcis-space-6)",
              backgroundColor: "var(--vcis-danger-bg)",
              border: "1px solid var(--vcis-danger-border)",
              color: "var(--vcis-danger-text)",
            }}
          >
            <h3 style={{ marginTop: 0, fontSize: "var(--vcis-text-base)", fontWeight: "var(--vcis-font-semibold)" }}>
              Profile Resolution Error
            </h3>
            <p style={{ margin: "var(--vcis-space-2) 0 0 0", fontSize: "var(--vcis-text-sm)" }}>{profileError}</p>
          </div>
        ) : student ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--vcis-space-6)" }}>
            {/* Student Identity Banner */}
            <div className="vcis-welcome-card">
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: "var(--vcis-space-4)",
                }}
              >
                <div>
                  <h1
                    style={{
                      margin: 0,
                      fontSize: "var(--vcis-text-2xl)",
                      fontWeight: "var(--vcis-font-bold)",
                      color: "var(--vcis-text-primary)",
                      letterSpacing: "-0.02em",
                    }}
                  >
                    Welcome, {student.name}
                  </h1>
                  <p
                    style={{
                      margin: "var(--vcis-space-1) 0 0 0",
                      fontSize: "var(--vcis-text-sm)",
                      color: "var(--vcis-text-muted)",
                    }}
                  >
                    {course ? `${course.name} (${course.code})` : "Enrolled Academic Program"}
                    {department ? ` • Department of ${department.name}` : ""}
                  </p>
                </div>

                <div className="vcis-meta-pill-group">
                  <div className="vcis-meta-pill">
                    <span>Roll Number:</span>
                    <strong>{student.roll_number}</strong>
                  </div>
                  <div className="vcis-meta-pill">
                    <span>Student ID:</span>
                    <strong>#{student.id}</strong>
                  </div>
                  <div className="vcis-meta-pill" style={{ borderColor: "var(--vcis-primary-border)" }}>
                    <span>Current Semester:</span>
                    <strong style={{ color: "var(--vcis-primary-text)" }}>Sem {student.current_semester}</strong>
                  </div>
                  <div className="vcis-meta-pill">
                    <span>Admission Year:</span>
                    <strong>{student.admission_year}</strong>
                  </div>
                  <div className="vcis-meta-pill">
                    <span>Institutional Email:</span>
                    <strong>{student.email}</strong>
                  </div>
                </div>
              </div>
            </div>

            {/* 1. Early Academic Prediction Hero Component (Visual Focal Point) */}
            <PredictionCard
              prediction={prediction}
              isLoading={isPredictionLoading}
              insufficientData={insufficientData}
              errorMessage={predictionError}
              onRefresh={() => fetchPrediction(student.id, student.current_semester)}
            />

            {/* 2. Academic Key Performance Indicators Row */}
            <AcademicKpiGrid
              currentSemester={student.current_semester}
              currentAttendance={prediction?.features?.current_attendance}
              currentCt1Average={prediction?.features?.current_ct1_average}
              currentAssignmentAverage={prediction?.features?.current_assignment_average}
              isLoading={isPredictionLoading}
            />

            {/* 3. Current Academic Performance & Early Indicators */}
            <AcademicOverview
              currentSemester={student.current_semester}
              attendance={prediction?.features?.current_attendance}
              assignmentAverage={prediction?.features?.current_assignment_average}
              ct1Average={prediction?.features?.current_ct1_average}
              previousSemesterScore={prediction?.features?.previous_semester_score}
              previousSemesterAttendance={prediction?.features?.previous_semester_attendance}
              isLoading={isPredictionLoading}
            />

            {/* 4. Attendance Records & Subject Compliance */}
            <AttendanceOverview
              performanceProfiles={performanceProfiles}
              overallAttendance={prediction?.features?.current_attendance}
              isLoading={isResultsLoading}
            />

            {/* 5. Assessments & Dynamic Results Breakdown */}
            <AssessmentResultSection
              summary={academicSummary}
              isLoading={isResultsLoading}
            />

            {/* 6. Semester Progression History */}
            <SemesterHistory
              studentId={student.id}
              currentSemester={student.current_semester}
              totalSemesters={course?.total_semesters || 4}
            />

            {/* 7. Assigned Academic Interventions (Strictly Read-Only) */}
            <InterventionList
              interventions={interventions}
              isLoading={isInterventionsLoading}
              errorMessage={interventionsError}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default StudentDashboard;
