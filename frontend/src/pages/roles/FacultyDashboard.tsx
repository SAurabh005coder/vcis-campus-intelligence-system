import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "../../auth/AuthContext";
import {
  type AssessmentCreateRequest,
  type AttendanceCreateRequest,
  type CourseInfo,
  type CreateInterventionRequest,
  type FacultyProfile,
  type UpdateInterventionRequest,
  createAssessmentRecord,
  createAttendanceRecord,
  createIntervention,
  getAllStudents,
  getCourses,
  getCurrentFacultyProfile,
  getDepartmentById,
  getDepartments,
  getStudentPredictionForFaculty,
  listInterventions,
  updateIntervention,
} from "../../api/facultyApi";
import {
  type DepartmentInfo,
  type StudentAcademicSummaryResponse,
  type StudentProfile,
  getStudentAcademicSummary,
} from "../../api/studentApi";
import type { PredictionResponse } from "../../api/predictionApi";
import type { InterventionResponse } from "../../api/interventionApi";

import { FacultyOverview } from "../../components/faculty/FacultyOverview";
import { StudentSelector } from "../../components/faculty/StudentSelector";
import { StudentAcademicReview } from "../../components/faculty/StudentAcademicReview";
import { FacultyPredictionCard } from "../../components/faculty/FacultyPredictionCard";
import { InterventionTable } from "../../components/faculty/InterventionTable";
import { InterventionForm } from "../../components/faculty/InterventionForm";
import { AttendanceEntryModal } from "../../components/faculty/AttendanceEntryModal";
import { AssessmentEntryModal } from "../../components/faculty/AssessmentEntryModal";

export const FacultyDashboard: React.FC = () => {
  const { user } = useAuth();

  // Institutional metadata
  const [departments, setDepartments] = useState<DepartmentInfo[]>([]);
  const [courses, setCourses] = useState<CourseInfo[]>([]);

  // Faculty profile & directory states
  const [faculty, setFaculty] = useState<FacultyProfile | null>(null);
  const [facultyDepartment, setFacultyDepartment] = useState<DepartmentInfo | null>(null);
  const [isProfileLoading, setIsProfileLoading] = useState(true);
  const [students, setStudents] = useState<StudentProfile[]>([]);
  const [isStudentsLoading, setIsStudentsLoading] = useState(true);

  // Active selection state
  const [selectedStudent, setSelectedStudent] = useState<StudentProfile | null>(null);

  // Selected student's dynamic academic summary & course/dept details
  const [academicSummary, setAcademicSummary] = useState<StudentAcademicSummaryResponse | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);

  // Prediction state for selected student
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [isPredictionLoading, setIsPredictionLoading] = useState(false);
  const [insufficientData, setInsufficientData] = useState(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);

  // Interventions state
  const [studentInterventions, setStudentInterventions] = useState<InterventionResponse[]>([]);
  const [myInterventions, setMyInterventions] = useState<InterventionResponse[]>([]);
  const [isInterventionsLoading, setIsInterventionsLoading] = useState(false);

  // Modal state
  const [isInterventionModalOpen, setIsInterventionModalOpen] = useState(false);
  const [isSubmittingIntervention, setIsSubmittingIntervention] = useState(false);
  const [isAttendanceModalOpen, setIsAttendanceModalOpen] = useState(false);
  const [isSubmittingAttendance, setIsSubmittingAttendance] = useState(false);
  const [isAssessmentModalOpen, setIsAssessmentModalOpen] = useState(false);
  const [isSubmittingAssessment, setIsSubmittingAssessment] = useState(false);

  // Notification banners
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load Faculty profile, departments, courses, and student list on mount
  const loadInitialData = useCallback(async () => {
    if (!user) return;
    setIsProfileLoading(true);
    setIsStudentsLoading(true);

    try {
      const [facProfile, depts, crs, studentsList] = await Promise.all([
        getCurrentFacultyProfile(user.id),
        getDepartments().catch(() => []),
        getCourses().catch(() => []),
        getAllStudents().catch(() => []),
      ]);

      setFaculty(facProfile);
      setDepartments(depts);
      setCourses(crs);
      setStudents(studentsList);

      if (facProfile?.department_id) {
        const foundDept = depts.find((d) => d.id === facProfile.department_id);
        if (foundDept) {
          setFacultyDepartment(foundDept);
        } else {
          getDepartmentById(facProfile.department_id).then(setFacultyDepartment).catch(() => null);
        }

        // Also fetch interventions assigned to this faculty
        listInterventions({ faculty_id: facProfile.id })
          .then((data) => setMyInterventions(data))
          .catch(() => setMyInterventions([]));
      }

      // Auto-select first student if available and none selected
      if (studentsList.length > 0 && !selectedStudent) {
        setSelectedStudent(studentsList[0]);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to load initial faculty dashboard data.");
      }
    } finally {
      setIsProfileLoading(false);
      setIsStudentsLoading(false);
    }
  }, [user, selectedStudent]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // When selected student changes, fetch dynamic academic summary & interventions
  useEffect(() => {
    if (!selectedStudent) {
      setPrediction(null);
      setAcademicSummary(null);
      setStudentInterventions([]);
      return;
    }

    setPrediction(null);
    setPredictionError(null);
    setInsufficientData(false);

    // Fetch dynamic academic summary
    setIsSummaryLoading(true);
    getStudentAcademicSummary(selectedStudent.id)
      .then((data) => setAcademicSummary(data))
      .catch(() => setAcademicSummary(null))
      .finally(() => setIsSummaryLoading(false));

    // Fetch student's intervention history
    setIsInterventionsLoading(true);
    listInterventions({ student_id: selectedStudent.id })
      .then((data) => setStudentInterventions(data))
      .catch(() => setStudentInterventions([]))
      .finally(() => setIsInterventionsLoading(false));
  }, [selectedStudent]);

  // Explicit action: Generate Early Prediction for selected student
  const handleGeneratePrediction = async () => {
    if (!selectedStudent) return;
    setIsPredictionLoading(true);
    setPredictionError(null);
    setInsufficientData(false);

    try {
      const res = await getStudentPredictionForFaculty(
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

  // Explicit action: Create Academic Intervention
  const handleCreateIntervention = async (payload: CreateInterventionRequest) => {
    setIsSubmittingIntervention(true);
    setErrorMessage(null);
    try {
      await createIntervention(payload);
      setSuccessMessage("Academic intervention assigned successfully.");
      setTimeout(() => setSuccessMessage(null), 4000);
      setIsInterventionModalOpen(false);

      // Refresh both student's interventions and faculty's overall interventions
      if (selectedStudent) {
        const refreshedStudentInterventions = await listInterventions({
          student_id: selectedStudent.id,
        });
        setStudentInterventions(refreshedStudentInterventions);
      }

      if (faculty) {
        const refreshedMyInterventions = await listInterventions({
          faculty_id: faculty.id,
        });
        setMyInterventions(refreshedMyInterventions);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to assign academic intervention.");
      }
      throw err;
    } finally {
      setIsSubmittingIntervention(false);
    }
  };

  // Explicit action: Update Intervention Workflow
  const handleUpdateIntervention = async (
    id: number,
    payload: UpdateInterventionRequest
  ) => {
    setErrorMessage(null);
    await updateIntervention(id, payload);
    setSuccessMessage("Intervention workflow status updated successfully.");
    setTimeout(() => setSuccessMessage(null), 4000);

    // Refresh both views
    if (selectedStudent) {
      const refreshedStudentInterventions = await listInterventions({
        student_id: selectedStudent.id,
      });
      setStudentInterventions(refreshedStudentInterventions);
    }

    if (faculty) {
      const refreshedMyInterventions = await listInterventions({
        faculty_id: faculty.id,
      });
      setMyInterventions(refreshedMyInterventions);
    }
  };

  // Explicit action: Record Student Attendance
  const handleCreateAttendance = async (payload: AttendanceCreateRequest) => {
    setIsSubmittingAttendance(true);
    setErrorMessage(null);
    try {
      await createAttendanceRecord(payload);
      setSuccessMessage("Attendance session recorded successfully.");
      setTimeout(() => setSuccessMessage(null), 4000);
      setIsAttendanceModalOpen(false);

      // Refresh student's dynamic academic summary so updated attendance records and percentages are displayed
      if (selectedStudent) {
        setIsSummaryLoading(true);
        try {
          const updatedSummary = await getStudentAcademicSummary(selectedStudent.id);
          setAcademicSummary(updatedSummary);
        } catch {
          // Keep existing summary if background refresh fails
        } finally {
          setIsSummaryLoading(false);
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to record attendance session.");
      }
      throw err;
    } finally {
      setIsSubmittingAttendance(false);
    }
  };

  // Explicit action: Record Student Assessment (CT1 or Assignment)
  const handleCreateAssessment = async (payload: AssessmentCreateRequest) => {
    setIsSubmittingAssessment(true);
    setErrorMessage(null);
    try {
      await createAssessmentRecord(payload);
      setSuccessMessage(`Assessment ${payload.assessment_name} recorded successfully.`);
      setTimeout(() => setSuccessMessage(null), 4000);
      setIsAssessmentModalOpen(false);

      // Refresh student's dynamic academic summary so updated assessment marks and percentages are displayed
      if (selectedStudent) {
        setIsSummaryLoading(true);
        try {
          const updatedSummary = await getStudentAcademicSummary(selectedStudent.id);
          setAcademicSummary(updatedSummary);
        } catch {
          // Keep existing summary if background refresh fails
        } finally {
          setIsSummaryLoading(false);
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to record assessment.");
      }
      throw err;
    } finally {
      setIsSubmittingAssessment(false);
    }
  };

  // Look up selected student's Course & Department info
  const selectedStudentCourse = selectedStudent
    ? courses.find((c) => c.id === selectedStudent.course_id) || null
    : null;
  const selectedStudentDepartment = selectedStudent
    ? departments.find((d) => d.id === selectedStudent.department_id) || null
    : null;

  return (
    <div>
      {/* Page Header */}
      <div className="vcis-page-header" style={{ marginBottom: "var(--space-6)" }}>
        <div>
          <h1 className="vcis-page-title">Academic Review Workspace</h1>
          <p className="vcis-page-subtitle">
            Review student performance, generate predictions, and manage academic interventions.
          </p>
        </div>
        <div>
          <button
            type="button"
            onClick={loadInitialData}
            className="vcis-button vcis-button-secondary vcis-button-sm"
            title="Reload student directory and academic records"
          >
            Refresh Data
          </button>
        </div>
      </div>

      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        {/* Success Banner */}
        {successMessage && (
          <div
            className="vcis-alert vcis-alert-success"
            style={{
              marginBottom: "var(--space-4)",
              padding: "var(--space-3) var(--space-4)",
              borderRadius: "var(--radius-md)",
              fontSize: "var(--font-sm)",
              display: "flex",
              alignItems: "center",
              gap: "var(--space-2)",
            }}
            role="status"
          >
            <span>✓</span>
            <span>{successMessage}</span>
          </div>
        )}

        {/* Global Error Banner */}
        {errorMessage && (
          <div
            className="vcis-error"
            style={{ marginBottom: "var(--space-4)" }}
            role="alert"
          >
            <span>⚠️</span>
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Faculty & Department Overview */}
        {isProfileLoading ? (
          <div className="vcis-card" style={{ padding: "var(--space-6)", textAlign: "center", color: "var(--vcis-text-muted)", marginBottom: "var(--space-6)" }}>
            <div className="vcis-spinner" aria-hidden="true" style={{ margin: "0 auto var(--space-2)" }} />
            <div style={{ fontSize: "var(--font-sm)" }}>Loading faculty profile...</div>
          </div>
        ) : (
          <FacultyOverview
            faculty={faculty}
            department={facultyDepartment}
            email={user?.email}
            totalStudents={students.length}
          />
        )}

        {/* 2-Column Dashboard Workspace */}
        <div className="vcis-faculty-layout">
          {/* Left Column: Student Selection & Profile Summary */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            <StudentSelector
              students={students}
              selectedStudent={selectedStudent}
              onSelectStudent={(s) => setSelectedStudent(s)}
              isLoading={isStudentsLoading}
              departments={departments}
              facultyDepartmentId={faculty?.department_id ?? null}
            />

            {selectedStudent && (
              <StudentAcademicReview
                student={selectedStudent}
                prediction={prediction}
                isLoading={isPredictionLoading}
                course={selectedStudentCourse}
                department={selectedStudentDepartment}
                academicSummary={academicSummary}
                isSummaryLoading={isSummaryLoading}
                onOpenAttendanceModal={() => setIsAttendanceModalOpen(true)}
                onOpenAssessmentModal={() => setIsAssessmentModalOpen(true)}
              />
            )}
          </div>

          {/* Right Column: Prediction Review & Intervention Management */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            <FacultyPredictionCard
              prediction={prediction}
              isLoading={isPredictionLoading}
              insufficientData={insufficientData}
              errorMessage={predictionError}
              onGeneratePrediction={handleGeneratePrediction}
              onOpenInterventionModal={() => setIsInterventionModalOpen(true)}
              selectedStudentId={selectedStudent?.id || null}
            />

            <InterventionTable
              interventions={studentInterventions}
              myInterventions={myInterventions}
              isLoading={isInterventionsLoading}
              onUpdateIntervention={handleUpdateIntervention}
              studentName={selectedStudent?.name}
              currentFacultyId={faculty?.id ?? null}
              students={students}
            />
          </div>
        </div>

        {/* Attendance Entry Modal */}
        {isAttendanceModalOpen && selectedStudent && (
          <AttendanceEntryModal
            student={selectedStudent}
            enrollments={academicSummary?.subjects || []}
            onSubmit={handleCreateAttendance}
            onClose={() => setIsAttendanceModalOpen(false)}
            isSubmitting={isSubmittingAttendance}
          />
        )}

        {/* Assessment Entry Modal (CT1 and Assignment) */}
        {isAssessmentModalOpen && selectedStudent && (
          <AssessmentEntryModal
            student={selectedStudent}
            enrollments={academicSummary?.subjects || []}
            onSubmit={handleCreateAssessment}
            onClose={() => setIsAssessmentModalOpen(false)}
            isSubmitting={isSubmittingAssessment}
          />
        )}

        {/* Intervention Modal */}
        {isInterventionModalOpen && selectedStudent && prediction && faculty && (
          <InterventionForm
            student={selectedStudent}
            facultyId={faculty.id}
            prediction={prediction}
            onSubmit={handleCreateIntervention}
            onClose={() => setIsInterventionModalOpen(false)}
            isSubmitting={isSubmittingIntervention}
          />
        )}
      </div>
    </div>
  );
};

export default FacultyDashboard;
