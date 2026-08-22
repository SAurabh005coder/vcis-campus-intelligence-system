import { useEffect, useState } from "react";
import type { SubmitEvent } from "react";
import {
  createStudent,
  deleteStudent,
  getStudents,
  updateStudent,
  type Student,
} from "../../api/students";
import { getApiErrorMessage } from "../../api/errors";

function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [editingStudentId, setEditingStudentId] = useState<number | null>(
    null
  );

  useEffect(() => {
    async function loadStudents() {
      try {
        const data = await getStudents();
        setStudents(data);
      } catch {
        setError("Failed to load students.");
      } finally {
        setLoading(false);
      }
    }

    loadStudents();
  }, []);

  function handleEdit(student: Student) {
    setEditingStudentId(student.id);
    setName(student.name);
    setEmail(student.email);
    setError("");
  }

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    setSubmitting(true);
    setError("");

    try {
      if (editingStudentId === null) {
        const newStudent = await createStudent(name, email);

        setStudents((currentStudents) => [
          ...currentStudents,
          newStudent,
        ]);
      } else {
        const updatedStudent = await updateStudent(
          editingStudentId,
          name,
          email
        );

        setStudents((currentStudents) =>
          currentStudents.map((student) =>
            student.id === updatedStudent.id
              ? updatedStudent
              : student
          )
        );

        setEditingStudentId(null);
      }

      setName("");
      setEmail("");
   } catch (error) {
  setError(
    getApiErrorMessage(error, "Failed to save student.")
  );
} finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(studentId: number) {
    try {
      setError("");

      await deleteStudent(studentId);

      setStudents((currentStudents) =>
        currentStudents.filter(
          (student) => student.id !== studentId
        )
      );

      if (editingStudentId === studentId) {
        setEditingStudentId(null);
        setName("");
        setEmail("");
      }
    } catch (error) {
  setError(
    getApiErrorMessage(error, "Failed to delete student.")
  );
}
  }

  function handleCancelEdit() {
    setEditingStudentId(null);
    setName("");
    setEmail("");
    setError("");
  }

  return (
    <div>
      <h1>VCIS</h1>
      <p>Virtual Campus Intelligence System</p>

      <h2>
        {editingStudentId === null
          ? "Add Student"
          : "Edit Student"}
      </h2>

      <form onSubmit={handleSubmit}>
        <div>
          <label>
            Name:
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </label>
        </div>

        <div>
          <label>
            Email:
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
        </div>

        <button type="submit" disabled={submitting}>
          {submitting
            ? "Saving..."
            : editingStudentId === null
              ? "Add Student"
              : "Update Student"}
        </button>

        {editingStudentId !== null && (
          <button
            type="button"
            onClick={handleCancelEdit}
          >
            Cancel
          </button>
        )}
      </form>

      {error && <p>{error}</p>}

      <h2>Students</h2>

      {loading && <p>Loading students...</p>}

      {!loading && !error && (
        <>
          {students.length === 0 ? (
            <p>No students found.</p>
          ) : (
            students.map((student) => (
              <div key={student.id}>
                <p>Name: {student.name}</p>
                <p>Email: {student.email}</p>

                <button
                  type="button"
                  onClick={() => handleEdit(student)}
                >
                  Edit
                </button>

                <button
                  type="button"
                  onClick={() => handleDelete(student.id)}
                >
                  Delete
                </button>

                <hr />
              </div>
            ))
          )}
        </>
      )}
    </div>
  );
}

export default StudentsPage;