# VCIS 3.0 — AI-POWERED CAMPUS INTELLIGENCE SYSTEM
## Comprehensive Static & Structural Software Audit Report

**Date of Audit:** September 18, 2026  
**Project:** VCIS 3.0 (AI-Powered Campus Intelligence System — MCA 3rd Semester Minor Project)  
**Audit Type:** Complete Static & Structural Repository Audit (Backend, Frontend, Database, Migrations, ML/Feature Pipelines, Security, Contracts)  
**Target Audience:** Engineering Team & AI Integration Assistants  

---

## TABLE OF CONTENTS
1. [Section 1 — Project Inventory](#section-1--project-inventory)
2. [Section 2 — Technology Stack](#section-2--technology-stack)
3. [Section 3 — Backend Architecture](#section-3--backend-architecture)
4. [Section 4 — Database Architecture & Migrations](#section-4--database-architecture--migrations)
5. [Section 5 — Authentication & Authorization](#section-5--authentication--authorization)
6. [Section 6 — Current Academic Data Flow](#section-6--current-academic-data-flow)
7. [Section 7 — Assessment System](#section-7--assessment-system)
8. [Section 8 — Result System](#section-8--result-system)
9. [Section 9 — Current ML & Feature Engineering Pipeline](#section-9--current-ml--feature-engineering-pipeline)
10. [Section 10 — ML Integration Gap Analysis](#section-10--ml-integration-gap-analysis)
11. [Section 11 — Prediction Trigger Design](#section-11--prediction-trigger-design)
12. [Section 12 — Prediction Persistence Architecture](#section-12--prediction-persistence-architecture)
13. [Section 13 — Academic Intervention System](#section-13--academic-intervention-system)
14. [Section 14 — Frontend Audit](#section-14--frontend-audit)
15. [Section 15 — API ↔ Frontend Contract Analysis](#section-15--api--frontend-contract-analysis)
16. [Section 16 — Testing & Quality Assurance](#section-16--testing--quality-assurance)
17. [Section 17 — Configuration & Environment](#section-17--configuration--environment)
18. [Section 18 — Code Quality & Structural Observations](#section-18--code-quality--structural-observations)
19. [Section 19 — Current System Architecture Diagram](#section-19--current-system-architecture-diagram)
20. [Section 20 — Current vs Required Architecture Comparison](#section-20--current-vs-required-architecture-comparison)
21. [Section 21 — ML Feature Compatibility Audit](#section-21--ml-feature-compatibility-audit)
22. [Section 22 — Data Leakage Audit](#section-22--data-leakage-audit)
23. [Section 23 — Database ↔ ML Mapping](#section-23--database--ml-mapping)
24. [Section 24 — Phased Modification & Implementation Plan](#section-24--phased-modification--implementation-plan)
25. [Section 25 — File-by-File Change Map](#section-25--file-by-file-change-map)
26. [Section 26 — Critical Issues (Blockers, High, Medium, Low)](#section-26--critical-issues)
27. [Section 27 — What is Already Working (Do Not Rewrite)](#section-27--what-is-already-working)
28. [Section 28 — Unknown / Needs Runtime Verification](#section-28--unknown--needs-runtime-verification)
29. [Section 29 — Final Executive Summary](#section-29--final-executive-summary)

---

## SECTION 1 — PROJECT INVENTORY

### 1.1 Complete Project Tree
```
VCIS 3.0/
├── README.md                                    # High-level project summary and test credentials
├── .gitignore                                   # Root git ignore rules
├── backend/
│   ├── .env                                     # Local environment config (DB URL, JWT secrets)
│   ├── alembic.ini                              # Alembic migration configuration
│   ├── requirements.txt                         # Python package requirements
│   ├── package.json                             # Accidental npm manifest in backend (contains alembic npm)
│   ├── package-lock.json                        # Accidental npm lockfile in backend
│   ├── alembic/
│   │   ├── env.py                               # Alembic runtime environment & model registration
│   │   ├── README                               # Generic Alembic readme
│   │   ├── script.py.mako                       # Mako migration script template
│   │   └── versions/                            # 10 migration versions (Linear history)
│   │       ├── bb08fe3dbc35_create_students_table.py
│   │       ├── 73bc81b700d6_create_users_table.py
│   │       ├── 84083e6171fa_create_departments_table.py
│   │       ├── 27b546553e39_create_faculty_table.py
│   │       ├── 27e208707eef_create_courses_table.py
│   │       ├── eed25aa6fde4_create_subjects_table.py
│   │       ├── 9a0b9ad7329b_extend_students_academic_profile.py
│   │       ├── f436ef953025_create_enrollments_table.py
│   │       ├── 4e6429659cf1_create_attendance_table.py
│   │       └── 5ef3d75a843a_create_assessments_table.py
│   └── app/
│       ├── base.py                              # DeclarativeBase definition
│       ├── database.py                          # SQLAlchemy engine & SessionLocal sessionmaker, get_db()
│       ├── main.py                              # FastAPI app entry point, CORS, routers, health checks
│       ├── test_db.py                           # Standalone database connectivity check script
│       ├── core/
│       │   ├── authorization.py                 # require_roles(*roles) RBAC dependency
│       │   ├── dependencies.py                  # get_current_user JWT token extraction & verification
│       │   └── security.py                      # Password hashing & verification using pwdlib (Argon2)
│       ├── models/
│       │   ├── assessment.py                    # Assessment ORM Model (AssessmentType Enum)
│       │   ├── attendance.py                    # Attendance ORM Model (AttendanceStatus Enum)
│       │   ├── course.py                        # Course ORM Model
│       │   ├── department.py                    # Department ORM Model
│       │   ├── enrollment.py                    # Enrollment ORM Model (EnrollmentStatus Enum)
│       │   ├── faculty.py                       # Faculty ORM Model
│       │   ├── student.py                       # Student ORM Model
│       │   ├── subject.py                       # Subject ORM Model
│       │   └── user.py                          # User ORM Model (UserRole Enum)
│       ├── routers/
│       │   ├── assessments.py                   # /api/v1/assessments CRUD
│       │   ├── attendance.py                    # /api/v1/attendance CRUD
│       │   ├── auth.py                          # /api/v1/auth/login JWT issuance
│       │   ├── courses.py                       # /api/v1/courses CRUD
│       │   ├── departments.py                   # /api/v1/departments CRUD
│       │   ├── enrollments.py                   # /api/v1/enrollments CRUD
│       │   ├── faculty.py                       # /api/v1/faculty CRUD
│       │   ├── results.py                       # /api/v1/results calculation endpoints
│       │   ├── students.py                      # /api/v1/students CRUD
│       │   ├── subjects.py                      # /api/v1/subjects CRUD
│       │   └── users.py                         # /api/v1/users creation and /me profile
│       ├── schemas/
│       │   ├── assessment.py                    # Assessment Pydantic schemas (Create, Update, Response)
│       │   ├── attendance.py                    # Attendance Pydantic schemas
│       │   ├── auth.py                          # LoginRequest, TokenResponse schemas
│       │   ├── course.py                        # Course schemas
│       │   ├── department.py                    # Department schemas
│       │   ├── enrollment.py                    # Enrollment schemas
│       │   ├── faculty.py                       # Faculty schemas
│       │   ├── result.py                        # Result calculation response schemas
│       │   ├── student.py                       # Student schemas
│       │   ├── subject.py                       # Subject schemas
│       │   └── user.py                          # User schemas
│       └── services/
│           ├── feature_service.py               # get_enrollment_ml_features (Orphaned / Subject-level)
│           └── result_service.py                # Academic result & attendance aggregation engine
├── frontend/
│   ├── .gitignore                               # Frontend git ignore rules
│   ├── eslint.config.js                         # ESLint configuration
│   ├── index.html                               # SPA HTML template
│   ├── package.json                             # Frontend dependencies & scripts
│   ├── package-lock.json                        # Frontend npm lockfile
│   ├── README.md                                # Frontend Vite README
│   ├── tsconfig.json                            # TypeScript root config
│   ├── tsconfig.app.json                        # TypeScript client app config
│   ├── tsconfig.node.json                       # TypeScript Vite node config
│   ├── vite.config.ts                           # Vite configuration
│   ├── public/
│   │   ├── favicon.svg                          # Public favicon
│   │   └── icons.svg                            # Public icon sprite
│   └── src/
│       ├── App.css                              # App stylesheet (empty)
│       ├── App.tsx                              # React Router router setup
│       ├── index.css                            # Base typography and margin styles
│       ├── main.tsx                             # React DOM entry point
│       ├── api/
│       │   ├── client.ts                        # Axios instance (baseURL: http://127.0.0.1:8000, NO auth headers)
│       │   ├── errors.ts                        # Axios error code to message translator
│       │   └── students.ts                      # Student API client functions (Legacy 2-field shape)
│       ├── assets/
│       │   ├── hero.png                         # Hero graphic
│       │   ├── react.svg                        # React logo
│       │   └── vite.svg                         # Vite logo
│       ├── layouts/
│       │   └── AppLayout.tsx                    # Minimal header and navigation shell
│       └── pages/
│           ├── HomePage.tsx                     # Minimal placeholder landing page
│           └── students/
│               └── StudentsPage.tsx             # Legacy Student CRUD page (Incompatible with backend)
├── database/                                    # Empty directory (no raw SQL scripts or dump files)
├── docs/                                        # Empty directory (no markdown/PDF documentation)
└── tests/                                       # Empty directory (no backend or frontend tests)
```

### 1.2 File-by-File Inventory Details

| File Path | File Type | Purpose | Active Status | Important Dependencies / Imports | Relationships |
|---|---|---|---|---|---|
| `README.md` | Markdown | Basic project overview & test credentials | Active | None | Documents login credentials |
| `backend/.env` | Config / Env | Environment variables for DB & JWT | Active | None | Read by `database.py`, `dependencies.py`, `auth.py`, `alembic/env.py` |
| `backend/alembic.ini` | Config | Migration tool configuration | Active | Alembic | Directs Alembic to `backend/alembic` |
| `backend/package.json` | Config / JSON | Accidental npm manifest | Dead / Unused | `"alembic": "^0.0.3"` | Created accidentally by developer running npm in backend |
| `backend/requirements.txt` | Config | Python dependency list | Active | FastAPI, SQLAlchemy, Pydantic, etc. | Python environment specification |
| `backend/alembic/env.py` | Python Script | Alembic migration runner | Active | `app.base.Base`, all ORM models | Binds Alembic migrations to Base.metadata |
| `backend/alembic/versions/*.py` | Python Migrations | Database schema migration history (10 revisions) | Active | `alembic.op`, `sqlalchemy` | Creates DB tables and foreign keys |
| `backend/app/base.py` | Python Module | Declarative Base for SQLAlchemy | Active | `sqlalchemy.orm.DeclarativeBase` | Inherited by all ORM models |
| `backend/app/database.py` | Python Module | SQLAlchemy DB Engine, Session, `get_db` | Active | `create_engine`, `sessionmaker`, `os.getenv` | Injected into all routers |
| `backend/app/main.py` | Python Module | FastAPI App initialization, CORS, routing | Active | `FastAPI`, `CORSMiddleware`, all routers | Main entry point for `uvicorn` |
| `backend/app/test_db.py` | Python Script | Standalone DB connection diagnostic | Utility | `app.database.engine` | Manual diagnostic tool |
| `backend/app/core/authorization.py` | Python Module | `require_roles(*roles)` RBAC wrapper | Active | `fastapi.Depends`, `get_current_user`, `UserRole` | Used by all secured routers |
| `backend/app/core/dependencies.py` | Python Module | `get_current_user` JWT validation dependency | Active | `jwt`, `HTTPBearer`, `app.models.user.User` | Authenticates requests |
| `backend/app/core/security.py` | Python Module | Password hashing & verification with Argon2 | Active | `pwdlib.PasswordHash` | Used by `users.py` and `auth.py` |
| `backend/app/models/user.py` | Python ORM | `User` table model & `UserRole` enum | Active | `app.base.Base`, `sqlalchemy` | Referenced by `Student`, `Faculty` |
| `backend/app/models/department.py` | Python ORM | `Department` table model | Active | `app.base.Base` | Referenced by `Course`, `Faculty`, `Student` |
| `backend/app/models/course.py` | Python ORM | `Course` table model | Active | `Department` FK | Referenced by `Subject`, `Student` |
| `backend/app/models/faculty.py` | Python ORM | `Faculty` table model | Active | `User` FK, `Department` FK | Faculty profile mapping |
| `backend/app/models/student.py` | Python ORM | `Student` table model | Active | `User` FK, `Department` FK, `Course` FK | Referenced by `Enrollment` |
| `backend/app/models/subject.py` | Python ORM | `Subject` table model | Active | `Course` FK | Referenced by `Enrollment` |
| `backend/app/models/enrollment.py` | Python ORM | `Enrollment` table model & `EnrollmentStatus` | Active | `Student` FK, `Subject` FK | Referenced by `Attendance`, `Assessment` |
| `backend/app/models/attendance.py` | Python ORM | `Attendance` table model & `AttendanceStatus` | Active | `Enrollment` FK | Attendance transaction records |
| `backend/app/models/assessment.py` | Python ORM | `Assessment` table model & `AssessmentType` | Active | `Enrollment` FK | Academic assessment marks |
| `backend/app/schemas/*.py` | Python Pydantic | Request/Response DTO validation schemas | Active | `pydantic.BaseModel`, `Field`, `ConfigDict` | Serializes/validates router data |
| `backend/app/services/result_service.py` | Python Service | Result calculation, GPA/credits, attendance % | Active | `Enrollment`, `Subject`, `Assessment`, `Attendance` | Called by `results.py` router |
| `backend/app/services/feature_service.py` | Python Service | Legacy enrollment feature extractor | Orphaned / Unused | `Student`, `Enrollment`, `Assessment`, `Attendance` | Not called by any router |
| `backend/app/routers/*.py` | Python Routers | REST API endpoint handlers (11 routers) | Active | FastAPI, Schemas, Models, Core auth | Included in `main.py` |
| `frontend/src/api/client.ts` | TypeScript | Axios HTTP client instance | Active | `axios` | Used by frontend API services |
| `frontend/src/api/errors.ts` | TypeScript | HTTP error code status to string mapper | Active | `axios` | Used in `StudentsPage.tsx` |
| `frontend/src/api/students.ts` | TypeScript | Student API consumer functions | Active (Broken) | `client.ts` | Calls `/api/v1/students/` |
| `frontend/src/layouts/AppLayout.tsx` | TSX Component | Shell layout with header & router outlet | Active | `react-router-dom` | Layout wrapper in `App.tsx` |
| `frontend/src/pages/HomePage.tsx` | TSX Component | Static landing page | Active | React | Home route (`/`) |
| `frontend/src/pages/students/StudentsPage.tsx` | TSX Component | Student management UI form & table | Active (Broken) | `students.ts`, React hooks | Student route (`/students`) |

---

## SECTION 2 — TECHNOLOGY STACK

| Layer / Subsystem | Technology | Declared Version | Actual Usage Status | Evidence / File Source |
|---|---|---|---|---|
| **Language Runtime (Backend)** | Python | `>= 3.10` (type unions `str \| None`) | ACTUALLY USED | `backend/app/models/*.py`, `typing` syntax |
| **Web Framework** | FastAPI | `0.141.1` | ACTUALLY USED | `backend/app/main.py`, `backend/requirements.txt` |
| **ASGI Server** | Uvicorn | `0.52.3` | ACTUALLY USED | `backend/requirements.txt`, `README.md` |
| **Data Validation / DTO** | Pydantic (Core + Settings) | `2.13.4` (Core `2.46.4`) | ACTUALLY USED | `backend/app/schemas/*.py` |
| **ORM Layer** | SQLAlchemy 2.0 | `2.0.52` | ACTUALLY USED | `Mapped`, `mapped_column` in all models |
| **Database Engine** | PostgreSQL | PostgreSQL 14+ compatible | ACTUALLY USED | `backend/.env` (`postgresql+psycopg://`) |
| **Database Driver** | psycopg (v3 binary) | `3.3.4` | ACTUALLY USED | `requirements.txt`, `.env` connection string |
| **Database Migrations** | Alembic | `1.13+` (runtime) | ACTUALLY USED | `backend/alembic.ini`, `backend/alembic/` |
| **Password Hashing** | pwdlib (Argon2) | default | ACTUALLY USED | `backend/app/core/security.py` |
| **Token / Authentication** | PyJWT | default (`HS256`) | ACTUALLY USED | `backend/app/routers/auth.py`, `dependencies.py` |
| **Environment Config** | python-dotenv | `1.2.3` | ACTUALLY USED | `backend/app/database.py`, `alembic/env.py` |
| **Frontend Framework** | React | `19.2.8` | ACTUALLY USED | `frontend/package.json`, `frontend/src/main.tsx` |
| **Frontend Language** | TypeScript | `6.0.2` (~6.0) | ACTUALLY USED | `frontend/tsconfig.json`, `src/**/*.tsx` |
| **Build Tool / Bundler** | Vite | `8.2.0` | ACTUALLY USED | `frontend/vite.config.ts` |
| **Routing** | React Router DOM | `7.18.2` | ACTUALLY USED | `frontend/src/App.tsx` |
| **HTTP Client** | Axios | `1.19.0` | ACTUALLY USED | `frontend/src/api/client.ts` |
| **CSS / Styling** | Plain CSS / Vanilla | N/A | ACTUALLY USED | `frontend/src/index.css`, `frontend/src/App.css` |
| **ML Libraries (Production)** | `scikit-learn`, `joblib`, `pandas`, `numpy` | Missing from requirements | **DECLARED BUT UNUSED IN REPO** | Required by Colab models, missing in `backend/requirements.txt` |
| **Testing Frameworks** | `pytest`, `jest`, `vitest` | None installed | **NOT PRESENT** | `tests/` directory is empty |
| **Containerization** | Docker / Docker Compose | None | **NOT PRESENT** | No `Dockerfile` or `docker-compose.yml` found |

---

## SECTION 3 — BACKEND ARCHITECTURE

### 3.1 Architecture Overview & Entry Point
- **Entry Point:** `backend/app/main.py` creates the `app = FastAPI()` instance.
- **Middleware:** `CORSMiddleware` configured with `allow_origins=["http://localhost:5173"]`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.
- **Health Checks:**
  - `GET /health` -> `{"status": "ok"}`
  - `GET /health/database` -> Executes `SELECT 1` via `engine.connect()` and returns database connectivity status.

### 3.2 Request Flow & Layering
```
Frontend (Axios HTTP Request)
    │
    ▼
FastAPI Routing Layer (app.main.py -> app.routers.*)
    │
    ├── Authentication & RBAC Layer (Depends(get_current_user), Depends(require_roles(*roles)))
    │       ├── PyJWT verification with JWT_SECRET_KEY
    │       └── Database lookup: User.is_active, User.role
    │
    ├── Request Validation Layer (Pydantic schemas in app.schemas.*)
    │
    ├── Service / Calculation Layer (app.services.result_service.py)
    │
    ├── ORM Persistence Layer (SQLAlchemy Mapped Models in app.models.*)
    │
    ▼
PostgreSQL Database (psycopg driver)
```

### 3.3 Dependency Injection Mechanism
1. **Database Session (`get_db`):** Defined in `app/database.py`. Yields a SQLAlchemy `Session` from `SessionLocal()`, and closes it in a `finally:` block.
2. **Current User (`get_current_user`):** Defined in `app/core/dependencies.py`. Uses `HTTPBearer()` scheme to extract the bearer token from the `Authorization` header, decodes payload using `JWT_SECRET_KEY` and `HS256`, validates user existence and `is_active` flag from database.
3. **Role-Based Access Control (`require_roles`):** Defined in `app/core/authorization.py`. Higher-order dependency function returning a closure that asserts `current_user.role in allowed_roles`, raising `HTTP 403 Forbidden` if unauthorized.

### 3.4 Registered API Router Breakdown

| Router / Prefix | Endpoint | Method | Request Schema | Response Schema | Required Roles | Service Called | DB Tables Accessed | Primary Validation & Limitations |
|---|---|---|---|---|---|---|---|---|
| **Auth**<br>`/api/v1/auth` | `/login` | `POST` | `LoginRequest` (`email`, `password`) | `TokenResponse` (`access_token`, `token_type`) | None (Public) | Direct | `users` | Validates password with Argon2; issues 30-min JWT. |
| **Users**<br>`/api/v1/users` | `/` | `POST` | `UserCreate` (`email`, `password`, `role`) | `UserResponse` | None (**Security Risk**) | Direct | `users` | Unprotected registration; hashes password with Argon2. |
| | `/me` | `GET` | None | `UserResponse` | Authenticated User | Direct | `users` | Returns current user profile. |
| | `/admin-test` | `GET` | None | `dict` | `ADMIN` | Direct | `users` | Simple RBAC test endpoint. |
| **Departments**<br>`/api/v1/departments` | `/` | `POST` | `DepartmentCreate` | `DepartmentResponse` | `ADMIN` | Direct | `departments` | Unique name & code. |
| | `/` | `GET` | None | `list[DepartmentResponse]` | `STUDENT`, `FACULTY`, `HOD`, `ADMIN` | Direct | `departments` | Returns all departments. No pagination. |
| | `/{id}` | `GET` | Path `id: int` | `DepartmentResponse` | `STUDENT`, `FACULTY`, `HOD`, `ADMIN` | Direct | `departments` | 404 if not found. |
| | `/{id}` | `PUT` | `DepartmentUpdate` | `DepartmentResponse` | `ADMIN` | Direct | `departments` | Updates name, code, description, is_active. |
| | `/{id}` | `DELETE` | Path `id: int` | None (204) | `ADMIN` | Direct | `departments` | Hard deletes department (will fail if FKs exist). |
| **Courses**<br>`/api/v1/courses` | `/` | `POST` | `CourseCreate` | `CourseResponse` | `ADMIN` | Direct | `courses`, `departments` | Validates department is active. |
| | `/` | `GET` | None | `list[CourseResponse]` | All 4 Roles | Direct | `courses` | Unpaginated list. |
| | `/{id}` | `GET` | Path `id: int` | `CourseResponse` | All 4 Roles | Direct | `courses` | 404 if not found. |
| | `/{id}` | `PUT` | `CourseUpdate` | `CourseResponse` | `ADMIN` | Direct | `courses`, `departments` | Unique name/code check excluding self. |
| | `/{id}` | `DELETE` | Path `id: int` | None (204) | `ADMIN` | Direct | `courses` | Hard delete. |
| **Faculty**<br>`/api/v1/faculty` | `/` | `POST` | `FacultyCreate` | `FacultyResponse` | `ADMIN` | Direct | `faculty`, `users`, `departments` | User must exist, have FACULTY role, and not have existing profile. |
| | `/` | `GET` | None | `list[FacultyResponse]` | All 4 Roles | Direct | `faculty` | Returns all faculty. |
| | `/{id}` | `GET` | Path `id: int` | `FacultyResponse` | All 4 Roles | Direct | `faculty` | 404 if not found. |
| | `/{id}` | `PUT` | `FacultyUpdate` | `FacultyResponse` | `ADMIN` | Direct | `faculty`, `departments` | Unique employee_code check. |
| | `/{id}` | `DELETE` | Path `id: int` | None (204) | `ADMIN` | Direct | `faculty` | Hard delete. |
| **Students**<br>`/api/v1/students` | `/` | `POST` | `StudentCreate` | `StudentResponse` | `ADMIN` | Direct | `students`, `users`, `departments`, `courses` | Validates User role is STUDENT, Department and Course are active and matched. |
| | `/` | `GET` | None | `list[StudentResponse]` | All 4 Roles | Direct | `students` | Returns all students (No filtering by department or student ownership). |
| | `/{id}` | `GET` | Path `id: int` | `StudentResponse` | All 4 Roles | Direct | `students` | Allows any student to read any other student (**IDOR risk**). |
| | `/{id}` | `PUT` | `StudentUpdate` | `StudentResponse` | `ADMIN` | Direct | `students`, `departments`, `courses` | Validates department/course alignment. |
| | `/{id}` | `DELETE` | Path `id: int` | None (204) | `ADMIN` | Direct | `students` | Hard delete. |
| **Subjects**<br>`/api/v1/subjects` | `/` | `POST` | `SubjectCreate` | `SubjectResponse` | `ADMIN` | Direct | `subjects`, `courses` | Unique code & unique (course_id, semester, name). |
| | `/` | `GET` | None | `list[SubjectResponse]` | All 4 Roles | Direct | `subjects` | Unpaginated list. |
| | `/{id}` | `GET` | Path `id: int` | `SubjectResponse` | All 4 Roles | Direct | `subjects` | 404 if not found. |
| | `/{id}` | `PUT` | `SubjectUpdate` | `SubjectResponse` | `ADMIN` | Direct | `subjects`, `courses` | Uniqueness validation. |
| | `/{id}` | `DELETE` | Path `id: int` | None (204) | `ADMIN` | Direct | `subjects` | Hard delete. |
| **Enrollments**<br>`/api/v1/enrollments` | `/` | `POST` | `EnrollmentCreate` | `EnrollmentResponse` | `ADMIN` | Direct | `enrollments`, `students`, `subjects` | Asserts Student active, Subject active, Subject belongs to Student's course and semester. Unique (student, subject, year). |
| | `/` | `GET` | None | `list[EnrollmentResponse]` | All 4 Roles | Direct | `enrollments` | Unpaginated. |
| | `/{id}` | `GET` | Path `id: int` | `EnrollmentResponse` | All 4 Roles | Direct | `enrollments` | 404 if not found. |
| | `/{id}` | `PUT` | `EnrollmentUpdate` | `EnrollmentResponse` | `ADMIN` | Direct | `enrollments` | Updates status (ENROLLED, COMPLETED, DROPPED). |
| | `/{id}` | `DELETE` | Path `id: int` | None (204) | `ADMIN` | Direct | `enrollments` | Hard delete. |
| **Attendance**<br>`/api/v1/attendance` | `/` | `POST` | `AttendanceCreate` | `AttendanceResponse` | `ADMIN`, `FACULTY` | Direct | `attendance`, `enrollments` | Validates enrollment is active and enrolled; unique (enrollment_id, date). |
| | `/` | `GET` | None | `list[AttendanceResponse]` | All 4 Roles | Direct | `attendance` | Unfiltered list of all attendance records in institution. |
| | `/{id}` | `GET` | Path `id: int` | `AttendanceResponse` | All 4 Roles | Direct | `attendance` | Record lookup. |
| | `/{id}` | `PUT` | `AttendanceUpdate` | `AttendanceResponse` | `ADMIN`, `FACULTY` | Direct | `attendance` | Updates status & remarks. |
| | `/{id}` | `DELETE` | Path `id: int` | None (204) | `ADMIN` | Direct | `attendance` | Hard delete. |
| **Assessments**<br>`/api/v1/assessments` | `/` | `POST` | `AssessmentCreate` | `AssessmentResponse` | `FACULTY`, `ADMIN` | Direct | `assessments`, `enrollments` | Validates enrollment is ENROLLED; obtained_marks <= max_marks; unique (enrollment, type, name). |
| | `/` | `GET` | None | `list[AssessmentResponse]` | All 4 Roles | Direct | `assessments` | Unfiltered list. |
| | `/{id}` | `GET` | Path `id: int` | `AssessmentResponse` | All 4 Roles | Direct | `assessments` | Record lookup. |
| | `/{id}` | `PUT` | `AssessmentUpdate` | `AssessmentResponse` | `FACULTY`, `ADMIN` | Direct | `assessments`, `enrollments` | obtained_marks <= max_marks. |
| | `/{id}` | `DELETE` | Path `id: int` | None (204) | `ADMIN` | Direct | `assessments` | Hard delete. |
| **Results**<br>`/api/v1/results` | `/enrollment/{id}` | `GET` | Path `enrollment_id: int` | `EnrollmentResultResponse` | All 4 Roles | `get_enrollment_result` | `enrollments`, `subjects`, `assessments` | Computes subject overall percentage & item breakdown. |
| | `/student/{id}/summary` | `GET` | Path `student_id: int` | `StudentAcademicSummaryResponse` | All 4 Roles | `get_student_academic_summary` | `enrollments`, `subjects`, `assessments` | Computes cumulative student score across all enrolled subjects. |
| | `/student/{id}/semester/{sem}` | `GET` | Path `student_id, semester` | `StudentSemesterResultResponse` | All 4 Roles | `get_student_semester_result` | `enrollments`, `subjects`, `assessments` | Aggregates subject results for specific semester; sums total credits & max marks. |
| | `/enrollment/{id}/performance` | `GET` | Path `enrollment_id: int` | `EnrollmentPerformanceProfileResponse` | All 4 Roles | `get_enrollment_performance_profile` | `enrollments`, `subjects`, `assessments`, `attendance` | Returns combined assessment percentage and attendance percentage for enrollment. |

---

## SECTION 4 — DATABASE ARCHITECTURE & MIGRATIONS

### 4.1 Table Specifications

#### 1. Table `users`
- **Columns:**
  - `id` (INTEGER, PK, Autoincrement, Index)
  - `email` (VARCHAR(255), NOT NULL, UNIQUE, Index)
  - `password_hash` (VARCHAR(255), NOT NULL)
  - `role` (ENUM: `'STUDENT'`, `'FACULTY'`, `'HOD'`, `'ADMIN'`, NOT NULL)
  - `is_active` (BOOLEAN, NOT NULL, DEFAULT `True`)
  - `created_at` (TIMESTAMP WITHOUT TIME ZONE, NOT NULL, DEFAULT `now()`)
  - `updated_at` (TIMESTAMP WITHOUT TIME ZONE, NOT NULL, DEFAULT `now()`)
- **Indexes & Constraints:** `PRIMARY KEY (id)`, `UNIQUE (email)`
- **Purpose:** System authentication accounts.

#### 2. Table `departments`
- **Columns:**
  - `id` (INTEGER, PK, Autoincrement, Index)
  - `name` (VARCHAR(150), NOT NULL, UNIQUE, Index)
  - `code` (VARCHAR(20), NOT NULL, UNIQUE, Index)
  - `description` (TEXT, NULLABLE)
  - `is_active` (BOOLEAN, NOT NULL, DEFAULT `True`)
  - `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
  - `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
- **Indexes & Constraints:** `PRIMARY KEY (id)`, `UNIQUE (name)`, `UNIQUE (code)`
- **Purpose:** Academic departments (e.g. Computer Applications, Management).

#### 3. Table `courses`
- **Columns:**
  - `id` (INTEGER, PK, Autoincrement, Index)
  - `department_id` (INTEGER, NOT NULL, FK -> `departments.id`, Index)
  - `name` (VARCHAR(150), NOT NULL, UNIQUE)
  - `code` (VARCHAR(30), NOT NULL, UNIQUE, Index)
  - `description` (TEXT, NULLABLE)
  - `duration_years` (INTEGER, NOT NULL)
  - `total_semesters` (INTEGER, NOT NULL)
  - `is_active` (BOOLEAN, NOT NULL, DEFAULT `True`)
  - `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
  - `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
- **Indexes & Constraints:** `PRIMARY KEY (id)`, `FOREIGN KEY (department_id) REFERENCES departments(id)`, `UNIQUE (name)`, `UNIQUE (code)`
- **Purpose:** Degree programs (e.g. MCA, BCA, B.Tech).

#### 4. Table `faculty`
- **Columns:**
  - `id` (INTEGER, PK, Autoincrement, Index)
  - `user_id` (INTEGER, NOT NULL, UNIQUE, FK -> `users.id`, Index)
  - `department_id` (INTEGER, NOT NULL, FK -> `departments.id`, Index)
  - `employee_code` (VARCHAR(30), NOT NULL, UNIQUE, Index)
  - `first_name` (VARCHAR(100), NOT NULL)
  - `last_name` (VARCHAR(100), NOT NULL)
  - `designation` (VARCHAR(100), NOT NULL)
  - `phone` (VARCHAR(20), NULLABLE)
  - `is_active` (BOOLEAN, NOT NULL, DEFAULT `True`)
  - `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
  - `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
- **Indexes & Constraints:** `PRIMARY KEY (id)`, `FOREIGN KEY (user_id) REFERENCES users(id)`, `FOREIGN KEY (department_id) REFERENCES departments(id)`, `UNIQUE (user_id)`, `UNIQUE (employee_code)`
- **Purpose:** Faculty profile and departmental affiliation.

#### 5. Table `students`
- **Columns:**
  - `id` (INTEGER, PK, Autoincrement, Index)
  - `user_id` (INTEGER, NOT NULL, UNIQUE, FK -> `users.id`, Index)
  - `department_id` (INTEGER, NOT NULL, FK -> `departments.id`, Index)
  - `course_id` (INTEGER, NOT NULL, FK -> `courses.id`, Index)
  - `roll_number` (VARCHAR(30), NOT NULL, UNIQUE, Index)
  - `admission_year` (INTEGER, NOT NULL)
  - `current_semester` (INTEGER, NOT NULL)
  - `name` (VARCHAR(100), NOT NULL)
  - `email` (VARCHAR(255), NOT NULL, UNIQUE)
  - `is_active` (BOOLEAN, NOT NULL, DEFAULT `True`)
  - `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
  - `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
- **Indexes & Constraints:** `PRIMARY KEY (id)`, `FOREIGN KEY (user_id) REFERENCES users(id)`, `FOREIGN KEY (department_id) REFERENCES departments(id)`, `FOREIGN KEY (course_id) REFERENCES courses(id)`, `UNIQUE (user_id)`, `UNIQUE (roll_number)`, `UNIQUE (email)`
- **Purpose:** Student profile, course affiliation, semester tracking.

#### 6. Table `subjects`
- **Columns:**
  - `id` (INTEGER, PK, Autoincrement, Index)
  - `course_id` (INTEGER, NOT NULL, FK -> `courses.id`, Index)
  - `name` (VARCHAR(150), NOT NULL)
  - `code` (VARCHAR(30), NOT NULL, UNIQUE, Index)
  - `semester` (INTEGER, NOT NULL)
  - `credits` (INTEGER, NOT NULL)
  - `description` (TEXT, NULLABLE)
  - `is_active` (BOOLEAN, NOT NULL, DEFAULT `True`)
  - `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
  - `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
- **Indexes & Constraints:** `PRIMARY KEY (id)`, `FOREIGN KEY (course_id) REFERENCES courses(id)`, `UNIQUE (code)`
- **Purpose:** Subject/Course catalog with semester mapping and credit values.

#### 7. Table `enrollments`
- **Columns:**
  - `id` (INTEGER, PK, Autoincrement, Index)
  - `student_id` (INTEGER, NOT NULL, FK -> `students.id`, Index)
  - `subject_id` (INTEGER, NOT NULL, FK -> `subjects.id`, Index)
  - `academic_year` (VARCHAR(9), NOT NULL, Index)
  - `enrollment_date` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
  - `status` (ENUM: `'ENROLLED'`, `'COMPLETED'`, `'DROPPED'`, NOT NULL, DEFAULT `'ENROLLED'`)
  - `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
  - `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
- **Indexes & Constraints:** `PRIMARY KEY (id)`, `FOREIGN KEY (student_id) REFERENCES students(id)`, `FOREIGN KEY (subject_id) REFERENCES subjects(id)`, `UNIQUE (student_id, subject_id, academic_year)` (`uq_student_subject_academic_year`)
- **Purpose:** Links a student to a specific subject in an academic year.

#### 8. Table `attendance`
- **Columns:**
  - `id` (INTEGER, PK, Autoincrement, Index)
  - `enrollment_id` (INTEGER, NOT NULL, FK -> `enrollments.id`, Index)
  - `attendance_date` (DATE, NOT NULL, Index)
  - `status` (ENUM: `'PRESENT'`, `'ABSENT'`, NOT NULL)
  - `remarks` (TEXT, NULLABLE)
  - `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
  - `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
- **Indexes & Constraints:** `PRIMARY KEY (id)`, `FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)`, `UNIQUE (enrollment_id, attendance_date)` (`uq_attendance_enrollment_date`)
- **Purpose:** Daily session-level attendance record per enrollment.

#### 9. Table `assessments`
- **Columns:**
  - `id` (INTEGER, PK, Autoincrement, Index)
  - `enrollment_id` (INTEGER, NOT NULL, FK -> `enrollments.id`, Index)
  - `assessment_type` (ENUM: `'INTERNAL'`, `'ASSIGNMENT'`, `'MIDTERM'`, `'FINAL'`, NOT NULL, Index)
  - `assessment_name` (VARCHAR(150), NOT NULL)
  - `max_marks` (INTEGER, NOT NULL)
  - `obtained_marks` (INTEGER, NOT NULL)
  - `assessment_date` (DATE, NOT NULL, Index)
  - `remarks` (TEXT, NULLABLE)
  - `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
  - `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT `now()`)
- **Indexes & Constraints:** `PRIMARY KEY (id)`, `FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)`, `UNIQUE (enrollment_id, assessment_type, assessment_name)` (`uq_enrollment_assessment`)
- **Purpose:** Stores marks for all assessments associated with a subject enrollment.

### 4.2 Textual Entity-Relationship (ER) Description
```
User (1) ────< (0..1) Faculty (N) ────> (1) Department
User (1) ────< (0..1) Student (N) ────> (1) Department
Department (1) ────< (N) Course (1) ────< (N) Subject
Student (1) ────< (N) Enrollment (N) ────> (1) Subject
Student (N) ────> (1) Course
Enrollment (1) ────< (N) Attendance
Enrollment (1) ────< (N) Assessment
```

### 4.3 Alembic Migration History & Critical Flaws

#### Migration Chain Order:
1. `bb08fe3dbc35` (`create_students_table`): Created initial students table (`id`, `name`, `email`).
2. `73bc81b700d6` (`create_users_table`): Created users table with auth fields.
3. `84083e6171fa` (`create_departments_table`): Created departments table.
4. `27b546553e39` (`create_faculty_table`): Created faculty table linked to users & departments.
5. `27e208707eef` (`create_courses_table`): Created courses table linked to departments.
6. `eed25aa6fde4` (`create_subjects_table`): Created subjects table linked to courses.
7. `9a0b9ad7329b` (`extend_students_academic_profile`): Added `user_id`, `department_id`, `course_id`, `roll_number`, `admission_year`, `current_semester`, `is_active`, `created_at`, `updated_at` to students table.
8. `f436ef953025` (`create_enrollments_table`): Created enrollments table with unique constraint.
9. `4e6429659cf1` (`create_attendance_table`): Created attendance table with unique (enrollment, date).
10. `5ef3d75a843a` (`create_assessments_table`): Created assessments table with unique (enrollment, type, name). **(CURRENT HEAD)**

#### Critical Migration Flaw in `9a0b9ad7329b`:
In file `backend/alembic/versions/9a0b9ad7329b_extend_students_academic_profile.py`:
- **Hardcoded Development IDs:** Lines 89–147 execute raw SQL with explicit hardcoded IDs:
  `WHERE s.id IN (3, 7, 8, 10, 11)`, `department_id = 4`, `course_id = 2`, and `roll_number = CASE id WHEN 1 THEN 'MCA2026001' WHEN 3 THEN 'MCA2026002'...`.
- **Runtime Failure on Non-Clean Databases:** Lines 157–180 perform a check:
  `if missing_count != 0: raise RuntimeError(...)`. If applied on any database that had test student IDs other than `{1, 3, 7, 8, 10, 11}`, the migration crashes.
- **Clean Database Behavior:** On a brand new database with zero students, `missing_count == 0`, so it succeeds, but the hardcoded assumption remains an anti-pattern in the version history.

---

## SECTION 5 — AUTHENTICATION AND AUTHORIZATION

### 5.1 Authentication Flow
1. **Endpoint:** `POST /api/v1/auth/login` receives `LoginRequest(email, password)`.
2. **Password Verification:** Queries `User` by `email`, verifies password against `password_hash` using `app.core.security.verify_password` (pwdlib Argon2).
3. **Token Generation:** Issues a JWT signed with `JWT_SECRET_KEY` and algorithm `HS256`. Token claims:
   ```json
   {
     "sub": "<user.id>",
     "email": "<user.email>",
     "role": "<user.role>",
     "exp": "<datetime.now(utc) + 30 minutes>"
   }
   ```
4. **Token Decoding & Verification:** `get_current_user` in `app/core/dependencies.py` intercepts `Authorization: Bearer <token>`, decodes claims, verifies signature and expiration, casts `sub` to `int`, and loads the `User` from PostgreSQL, ensuring `user.is_active is True`.

### 5.2 Role-Based Access Control (RBAC) Matrix

| Endpoint Group | Method | Path | Allowed Roles | Enforced By | Actual Behavioral Scope |
|---|---|---|---|---|---|
| **Auth** | POST | `/api/v1/auth/login` | Public | None | Issues JWT token |
| **Users** | POST | `/api/v1/users/` | Public | None | **CRITICAL:** Anyone can register as ADMIN, HOD, FACULTY, or STUDENT |
| | GET | `/api/v1/users/me` | Authenticated | `get_current_user` | Returns profile of current user |
| | GET | `/api/v1/users/admin-test` | ADMIN | `require_roles(ADMIN)` | Admin verification |
| **Departments** | POST, PUT, DELETE | `/api/v1/departments/*` | ADMIN | `require_roles(ADMIN)` | Administrative management |
| | GET | `/api/v1/departments/*` | STUDENT, FACULTY, HOD, ADMIN | `require_roles(...)` | All authenticated users can view |
| **Courses** | POST, PUT, DELETE | `/api/v1/courses/*` | ADMIN | `require_roles(ADMIN)` | Administrative management |
| | GET | `/api/v1/courses/*` | STUDENT, FACULTY, HOD, ADMIN | `require_roles(...)` | All authenticated users can view |
| **Faculty** | POST, PUT, DELETE | `/api/v1/faculty/*` | ADMIN | `require_roles(ADMIN)` | Administrative management |
| | GET | `/api/v1/faculty/*` | STUDENT, FACULTY, HOD, ADMIN | `require_roles(...)` | All authenticated users can view |
| **Students** | POST, PUT, DELETE | `/api/v1/students/*` | ADMIN | `require_roles(ADMIN)` | Administrative management |
| | GET | `/api/v1/students/` | STUDENT, FACULTY, HOD, ADMIN | `require_roles(...)` | **IDOR Risk:** Returns all students in institution |
| | GET | `/api/v1/students/{id}` | STUDENT, FACULTY, HOD, ADMIN | `require_roles(...)` | **IDOR Risk:** Any student can view any other student |
| **Subjects** | POST, PUT, DELETE | `/api/v1/subjects/*` | ADMIN | `require_roles(ADMIN)` | Administrative management |
| | GET | `/api/v1/subjects/*` | STUDENT, FACULTY, HOD, ADMIN | `require_roles(...)` | All authenticated users can view |
| **Enrollments**| POST, PUT, DELETE | `/api/v1/enrollments/*`| ADMIN | `require_roles(ADMIN)` | Administrative management |
| | GET | `/api/v1/enrollments/*`| STUDENT, FACULTY, HOD, ADMIN | `require_roles(...)` | Unfiltered list |
| **Attendance** | POST, PUT | `/api/v1/attendance/*` | ADMIN, FACULTY | `require_roles(ADMIN, FACULTY)` | Marking & editing attendance |
| | DELETE | `/api/v1/attendance/{id}`| ADMIN | `require_roles(ADMIN)` | Admin delete |
| | GET | `/api/v1/attendance/*` | STUDENT, FACULTY, HOD, ADMIN | `require_roles(...)` | Unfiltered list |
| **Assessments**| POST, PUT | `/api/v1/assessments/*`| FACULTY, ADMIN | `require_roles(FACULTY, ADMIN)`| Grade entry |
| | DELETE | `/api/v1/assessments/{id}`| ADMIN | `require_roles(ADMIN)` | Admin delete |
| | GET | `/api/v1/assessments/*`| STUDENT, FACULTY, HOD, ADMIN | `require_roles(...)` | Unfiltered list |
| **Results** | GET | `/api/v1/results/*` | STUDENT, FACULTY, HOD, ADMIN | `require_roles(...)` | Read calculation results |

### 5.3 Security Vulnerabilities & Findings
1. **Unprotected User Creation (`POST /api/v1/users/`):** There is no role restriction on user registration. Any external client can send `{"email": "attacker@evil.com", "password": "...", "role": "admin"}` and gain immediate administrative privileges.
2. **Insecure Direct Object Reference (IDOR):**
   - `GET /api/v1/students/{student_id}` does not verify that a user with `STUDENT` role is querying their own profile.
   - `GET /api/v1/results/student/{student_id}/semester/{semester}` allows any student to view the grades and marks of any other student.
3. **Frontend Token Omission:** `frontend/src/api/client.ts` does not attach bearer tokens to Axios requests. Consequently, all protected backend API calls fail with `401 Unauthorized` or `403 Forbidden` from the frontend UI.
4. **Duplicate Column Definition in `User` Model:** In `backend/app/models/user.py`, `updated_at` is defined twice (lines 55–59 and lines 61–66).

---

## SECTION 6 — CURRENT ACADEMIC DATA FLOW

```
1. Student Creation:
   User (Role: STUDENT) + Department + Course ──> Student Record Created (admission_year, current_semester, roll_number)

2. Subject Cataloguing:
   Course + Semester + Credits ──> Subject Record Created

3. Enrollment:
   Student + Subject + Academic Year ──> Enrollment Record Created (Status: ENROLLED)
   (Validates Subject.course_id == Student.course_id AND Subject.semester == Student.current_semester)

4. Attendance Recording:
   Enrollment + Date + Status (PRESENT/ABSENT) ──> Attendance Record Created

5. Assessment Recording:
   Enrollment + AssessmentType (INTERNAL/ASSIGNMENT/MIDTERM/FINAL) + Name + Obtained Marks + Max Marks
   ──> Assessment Record Created

6. Result & Performance Aggregation:
   - Subject Level: get_enrollment_result() aggregates marks across all assessments for that enrollment.
   - Semester Level: get_student_semester_result() joins Enrollments and Subjects for (student_id, semester)
     and calculates total max marks, total obtained marks, and semester overall percentage.
```

### Calculated vs Stored Data:
- **Stored Entities:** Student profiles, subjects, enrollments, individual attendance events, individual assessment marks.
- **Dynamically Calculated (Not Stored):**
  - Attendance percentage (present / total * 100)
  - Subject percentage (obtained / max * 100)
  - Semester overall percentage (sum obtained / sum max * 100)
  - Total semester credits

---

## SECTION 7 — ASSESSMENT SYSTEM

### 7.1 Current Model & Enum Representation
In `backend/app/models/assessment.py`:
```python
class AssessmentType(str, Enum):
    INTERNAL = "internal"
    ASSIGNMENT = "assignment"
    MIDTERM = "midterm"
    FINAL = "final"
```

### 7.2 How CT1, CT2, and Assignments Are Currently Handled
1. **Assignments:** Represented with `assessment_type = AssessmentType.ASSIGNMENT`.
2. **CT1 & CT2:** **There are NO explicit `CT1` or `CT2` enum values in `AssessmentType`!**
   - The current schema stores Class Tests under `assessment_type = AssessmentType.INTERNAL`, distinguishing them solely through arbitrary text strings in `assessment_name` (e.g. `"CT1"`, `"Class Test 1"`, `"CT-1"`, `"Internal Test 1"`).
3. **Midterm & Final:** Represented by `AssessmentType.MIDTERM` and `AssessmentType.FINAL`.

### 7.3 Fragility & Required Changes for Robust ML Feature Extraction
- **The Problem:** String matching on `assessment_name` (`LIKE '%CT1%'` or `== 'CT1'`) is fragile and prone to human error during data entry by faculty.
- **Required Solution (Documented, Not Modified):**
  - Option A: Extend `AssessmentType` enum in database & schemas to explicitly include `CT1`, `CT2`, `ASSIGNMENT`, `FINAL`, `MIDTERM`, `OTHER`.
  - Option B: Introduce an explicit structured subcategory / assessment code column (e.g. `category: Enum('CT1', 'CT2', 'ASSIGNMENT', 'FINAL')`) with database constraints.

---

## SECTION 8 — RESULT SYSTEM

### 8.1 Calculation Logic in `result_service.py`
1. **`get_enrollment_result(db, enrollment_id)`:**
   - Queries all assessments for `enrollment_id`.
   - `total_max_marks = sum(a.max_marks)`
   - `total_obtained_marks = sum(a.obtained_marks)`
   - `overall_percentage = (total_obtained_marks / total_max_marks) * 100`
   - Returns subject metadata, totals, and individual assessment percentages.
2. **`get_student_semester_result(db, student_id, semester)`:**
   - Joins `Enrollment` with `Subject` where `Subject.semester == semester` and `Enrollment.student_id == student_id`.
   - Sums `total_max_marks` and `total_obtained_marks` across all subjects in that semester.
   - `overall_percentage = (sum_obtained / sum_max) * 100`.
   - Sums `credits` across subjects.
3. **`get_enrollment_attendance(db, enrollment_id)`:**
   - Counts `PRESENT` and `ABSENT` records.
   - `attendance_percentage = (present / total) * 100`.

### 8.2 Early Prediction Features vs Post-Semester Final Outcomes

| Concept | Nature | Database Representation | Can Be Used in ML Prediction? |
|---|---|---|---|
| **Current Attendance** | Early Feature | `Attendance` records up to CT1 date | **YES** |
| **Current Assignment Avg** | Early Feature | `Assessment` where type is `ASSIGNMENT` | **YES** |
| **Current CT1 Avg** | Early Feature | `Assessment` where type/name is `CT1` | **YES** |
| **Previous Semester Score** | Historical Feature | Semester result from `semester - 1` | **YES (Sem 2–4 Only)** |
| **Previous Semester Attendance**| Historical Feature | Attendance % aggregated over `semester - 1` | **YES (Sem 2–4 Only)** |
| **CT2 Marks** | Intermediate Outcome | `Assessment` where type/name is `CT2` | **NO (Data Leakage)** |
| **Final Exam Marks** | Final Outcome / Target | `Assessment` where type is `FINAL` | **NO (Target Leakage)** |
| **Current Semester Result** | Final Outcome / Target | `result_service.get_student_semester_result` | **NO (Target Leakage)** |

---

## SECTION 9 — CURRENT ML / FEATURE ENGINEERING

### 9.1 Existing Feature Service Audit (`backend/app/services/feature_service.py`)
The existing function `get_enrollment_ml_features(db, enrollment_id)` calculates:
```python
# Assessment features (Enrollment / Single Subject Level)
total_max_marks = sum(a.max_marks for a in assessments)
total_obtained_marks = sum(a.obtained_marks for a in assessments)
assessment_percentage = (total_obtained_marks / total_max_marks) * 100

# Attendance features (Single Subject Level)
attendance_percentage = (present_classes / total_classes) * 100
```
And returns:
```python
{
    "student_id": student.id,
    "enrollment_id": enrollment.id,
    "subject_id": subject.id,
    "admission_year": student.admission_year,
    "current_semester": student.current_semester,
    "semester": subject.semester,
    "credits": subject.credits,
    "assessment_count": assessment_count,
    "total_max_marks": total_max_marks,
    "total_obtained_marks": total_obtained_marks,
    "assessment_percentage": round(assessment_percentage, 2),
    "total_classes": total_classes,
    "present_classes": present_classes,
    "absent_classes": absent_classes,
    "attendance_percentage": round(attendance_percentage, 2),
}
```

### 9.2 Comparison against Required ML Models

| Feature Name | Required by ML | Currently Available in `feature_service.py` | Current Source | Correct Aggregation Level? | Leakage Risk in Current Code | Required Changes |
|---|---|---|---|---|---|---|
| `current_attendance` | **YES** (Models 1 & 2) | **PARTIAL** (`attendance_percentage` per subject) | `attendance` table | **INCORRECT** (Subject-level, not student-semester level) | Low | Aggregate across all enrollments of student in current semester. |
| `current_assignment_average` | **YES** (Models 1 & 2) | **NO** | `assessments` table (lumped together) | **INCORRECT** (Lumped with all assessments) | **CRITICAL** (Includes CT2/Final if entered) | Filter strictly `assessment_type == 'ASSIGNMENT'` and average across subjects. |
| `current_ct1_average` | **YES** (Models 1 & 2) | **NO** | `assessments` table | **INCORRECT** (Not separated) | **CRITICAL** (Lumped) | Filter strictly CT1 assessments and average percentage across subjects. |
| `previous_semester_score` | **YES** (Model 2 Only) | **NO** | Not computed in feature service | **MISSING** | None | Compute `get_student_semester_result(student_id, current_semester - 1)['overall_percentage']`. |
| `previous_semester_attendance`| **YES** (Model 2 Only) | **NO** | Not computed in feature service | **MISSING** | None | Aggregate attendance for all enrollments in `current_semester - 1`. |
| `student_id` | **EXCLUDED** (Id only) | Included in dictionary | `student.id` | N/A | None | Must NOT be fed to `model.predict()`. |
| `final_semester_score` | **TARGET** | Lumped into `assessment_percentage` | `assessments` | **INCORRECT** | **CRITICAL** | Must be completely excluded from prediction feature vector. |

---

## SECTION 10 — ML INTEGRATION GAP ANALYSIS

### 10.1 Required Production Prediction Pipeline
```
Frontend (Dashboard / Student Profile / Early Warning View)
    │
    ▼
FastAPI Prediction Router (`POST /api/v1/predictions/student/{student_id}`)
    │
    ▼
Prediction Service (`app/services/prediction_service.py`)
    │
    ├── Step 1: Query Student Profile & determine current_semester
    │
    ├── Step 2: Feature Service (`app/services/feature_service.py`)
    │       ├── Semester 1 -> Extract [current_attendance, current_assignment_avg, current_ct1_avg]
    │       └── Semester 2-4 -> Extract [prev_score, prev_attendance, current_attendance, current_assignment_avg, current_ct1_avg]
    │
    ├── Step 3: Load Model Artifact (`vcis_models/vcis_model_semester*.joblib`)
    │       └── Singleton cache at application startup
    │
    ├── Step 4: Run Inference -> `predicted_final_score = model.predict(X)[0]`
    │
    ├── Step 5: Risk Level & Intervention Rule Evaluation
    │       ├── High Risk (< 50% or < 60%) -> Academic Intervention Recommended
    │       └── Status: INITIAL / EARLY_INTERVENTION
    │
    ├── Step 6: Persist into `predictions` Database Table
    │
    ▼
Response to Frontend & Update Academic Intelligence Dashboard
```

### 10.2 Architectural Components Required

| Component | Status in Codebase | What is Needed |
|---|---|---|
| **Model Artifacts Location** | Missing in repo | Store in `vcis_models/vcis_model_semester1.joblib` and `vcis_models/vcis_model_semesters2_4.joblib` |
| **Model Loader** | Missing | Startup singleton loader using `joblib.load()` stored in app state or service cache |
| **Feature Extraction Service** | Incompatible | Rewrite `feature_service.py` to extract student-semester level features adhering strictly to feature names and leakage prevention |
| **Prediction Service** | Missing | New `app/services/prediction_service.py` coordinating feature extraction, model selection (Sem 1 vs Sem 2–4), inference, and risk classification |
| **Prediction Schemas** | Missing | New `app/schemas/prediction.py` (`PredictionRequest`, `PredictionResponse`, `BatchPredictionResponse`) |
| **Prediction Database Table** | Missing | New Alembic migration + `app/models/prediction.py` |
| **Prediction Router** | Missing | New `app/routers/predictions.py` registered in `app/main.py` |
| **Intervention Database Table & APIs** | Missing | New `app/models/intervention.py`, `app/schemas/intervention.py`, `app/routers/interventions.py` |
| **Frontend ML Dashboard** | Missing | React dashboard displaying predictions, risk badges, feature breakdowns, and intervention actions |

---

## SECTION 11 — PREDICTION TRIGGER DESIGN

### 11.1 Business Logic & Eligibility Rules
1. **Semester 1 Trigger Conditions:**
   - Student is enrolled in Semester 1.
   - At least 1 attendance record exists in current semester.
   - Assignment assessments have been recorded.
   - **CT1 has been recorded** across current semester enrollments.
   - **CT2 and Final are NOT yet entered** (or strictly ignored by the feature extractor).
2. **Semesters 2–4 Trigger Conditions:**
   - Student is enrolled in Semester $K \in \{2, 3, 4\}$.
   - Semester $K-1$ academic history is finalized (used for `previous_semester_score` and `previous_semester_attendance`).
   - Current semester $K$ has attendance, assignments, and CT1 recorded.
3. **Trigger Invalidation:**
   - CT2 entry must NEVER trigger an early prediction.
   - Final exam entry must NEVER trigger an early prediction.

### 11.2 Best Integration Points in Backend
1. **Automatic Event Hook:** In `backend/app/routers/assessments.py`, when a `POST` or `PUT` creates/updates an assessment of category `CT1`, an event/task triggers `prediction_service.generate_early_prediction(student_id, semester)`.
2. **On-Demand On-Screen Trigger:** `POST /api/v1/predictions/student/{student_id}/generate` called by Faculty/HOD from the dashboard to evaluate student status.
3. **Batch Semester Trigger:** `POST /api/v1/predictions/batch/semester/{semester}` to compute risk scores for an entire cohort post-CT1.

---

## SECTION 12 — PREDICTION PERSISTENCE

### 12.1 Proposed Database Entity (`predictions`)
```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    semester INTEGER NOT NULL,
    prediction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    predicted_final_score NUMERIC(5, 2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL, -- 'LOW', 'MEDIUM', 'HIGH_RISK'
    model_version VARCHAR(50) NOT NULL, -- 'vcis_model_semester1_v1.0'
    prediction_trigger VARCHAR(50) NOT NULL, -- 'POST_CT1_AUTOMATIC', 'MANUAL_FACULTY', 'BATCH'
    features_snapshot JSONB NOT NULL, -- Stored input feature dictionary for auditability
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_semester_prediction_date UNIQUE (student_id, semester, prediction_date)
);
CREATE INDEX ix_predictions_student_semester ON predictions (student_id, semester);
```

---

## SECTION 13 — INTERVENTION SYSTEM

### 13.1 Academic Intervention Workflow
```
ML Early Prediction (Predicted Final Score < Threshold)
    │
    ▼
High Risk Academic Flag Raised (System Status: FLAGGED)
    │
    ▼
Faculty / HOD Dashboard Alert & Review
    │
    ▼
Intervention Assigned by Faculty:
    ├── Extra Class (Remedial Lectures)
    ├── Additional Assignment
    ├── Faculty Counselling
    └── Academic Monitoring
    │
    ▼
Intervention Tracking & Student Progress Monitoring
    │
    ▼
Intervention Resolution / Post-Intervention Evaluation
```

### 13.2 Proposed Database Entity (`interventions`)
```sql
CREATE TABLE interventions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    prediction_id INTEGER REFERENCES predictions(id) ON DELETE SET NULL,
    faculty_id INTEGER NOT NULL REFERENCES faculty(id),
    semester INTEGER NOT NULL,
    intervention_type VARCHAR(50) NOT NULL, -- 'EXTRA_CLASS', 'ADDITIONAL_ASSIGNMENT', 'COUNSELLING', 'MONITORING'
    status VARCHAR(30) NOT NULL DEFAULT 'ASSIGNED', -- 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'DISMISSED'
    description TEXT,
    action_plan TEXT,
    follow_up_date DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## SECTION 14 — FRONTEND AUDIT

### 14.1 Structure & Pages

| File Path | Component | Purpose | Current Functional Status | Connects to Backend? |
|---|---|---|---|---|
| `frontend/src/main.tsx` | Root Entry | Mounts React app into `#root` | Functional | N/A |
| `frontend/src/App.tsx` | Router Shell | Sets up `/` and `/students` routes | Functional | N/A |
| `frontend/src/layouts/AppLayout.tsx` | Layout | Navigation header (`Home`, `Students`) | Functional | N/A |
| `frontend/src/pages/HomePage.tsx` | Home Page | Placeholder text | Static only | No |
| `frontend/src/pages/students/StudentsPage.tsx` | Students Page | Student CRUD Form & List | **BROKEN** | Sends incomplete payload `{name, email}`; lacks auth token |

### 14.2 Missing Frontend Subsystems
- **No Login / Authentication Page:** No page for user login or storing JWT token in localStorage/sessionStorage.
- **No Role-Based Navigation:** No distinct views for Admin, Faculty, HOD, or Student.
- **No Faculty / Course / Department / Subject Management UI.**
- **No Attendance Marking UI.**
- **No Assessment / Grade Entry UI.**
- **No Result / Academic Summary Viewer.**
- **No ML Early Warning & Intervention Dashboard.**

---

## SECTION 15 — API ↔ FRONTEND CONTRACT

### 15.1 Contract Mapping

| Frontend Feature | Frontend API Call | Backend Endpoint | Request Payload Mismatch | Auth Header Attached? | Operational Status |
|---|---|---|---|---|---|
| **Load Students** | `getStudents()` in `src/api/students.ts` | `GET /api/v1/students/` | None (Query parameter mismatch) | **NO** (Missing Bearer Token) | **FAILS (401/403)** |
| **Add Student** | `createStudent(name, email)` | `POST /api/v1/students/` | **CRITICAL MISMATCH:** Frontend sends `{name, email}`. Backend requires `StudentCreate` (`user_id`, `department_id`, `course_id`, `roll_number`, `admission_year`, `current_semester`, `name`, `email`). | **NO** (Missing Bearer Token) | **FAILS (422 Unprocessable)** |
| **Update Student**| `updateStudent(id, name, email)` | `PUT /api/v1/students/{id}` | **CRITICAL MISMATCH:** Frontend sends `{name, email}`. Backend requires `StudentUpdate` with all academic fields. | **NO** (Missing Bearer Token) | **FAILS (422 Unprocessable)** |
| **Delete Student**| `deleteStudent(id)` | `DELETE /api/v1/students/{id}` | None | **NO** (Missing Bearer Token) | **FAILS (401/403)** |
| **All Other Backend APIs** | None | 10 other routers | No frontend callers exist | N/A | **UNUSED BY FRONTEND** |

---

## SECTION 16 — TESTING

### 16.1 Current Test Coverage
- **`tests/` Directory:** Completely empty.
- **Backend Tests:** 0 unit tests, 0 integration tests, 0 API tests.
- **Frontend Tests:** 0 tests.
- **Manual Diagnostic Script:** `backend/app/test_db.py` tests raw DB connection.

### 16.2 Essential Test Suites Required for ML Integration
1. **Feature Engineering Unit Tests:** Test Semester 1 and Semester 2–4 feature calculation against deterministic test fixtures.
2. **Data Leakage Tests:** Assert that adding CT2 and Final exam records does NOT alter early prediction feature values.
3. **Model Artifact Inference Tests:** Assert that loaded `.joblib` models output expected floats within valid score ranges (0–100).
4. **RBAC & Auth Tests:** Test token generation, role verification, and IDOR prevention.
5. **Academic Result Service Tests:** Test GPA, overall percentage, and credit aggregation.

---

## SECTION 17 — CONFIGURATION AND ENVIRONMENT

### 17.1 Environment Variables Audit

| Variable Name | Purpose | Configured in `backend/.env`? | Sample Format / Default |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | **YES (PRESENT)** | `postgresql+psycopg://user:password@localhost:5432/vcis` |
| `JWT_SECRET_KEY` | Symmetric HMAC key for JWT signing | **YES (PRESENT — VALUE REDACTED)** | `[REDACTED SECRET STRING]` |
| `JWT_ALGORITHM` | JWT signing algorithm | **YES (PRESENT)** | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration duration | **YES (PRESENT)** | `30` |

### 17.2 Configuration Files
- `backend/alembic.ini`: Properly points to `backend/alembic`.
- `backend/requirements.txt`: Contains core web & DB dependencies, but lacks ML dependencies (`joblib`, `scikit-learn`, `pandas`, `numpy`).
- `backend/package.json`: Extraneous/accidental file created by `npm i alembic` in backend directory.

---

## SECTION 18 — CODE QUALITY

### 18.1 Code Quality Findings & Anomalies
1. **Duplicate Column in Model:** `backend/app/models/user.py` contains duplicate `updated_at` attribute definition (lines 55–59 and 61–66).
2. **Duplicate Imports in Router:** `backend/app/routers/results.py` imports `get_enrollment_result`, `get_student_academic_summary`, etc., three times consecutively (lines 12–34).
3. **Orphaned Service:** `backend/app/services/feature_service.py` is never imported or called by any router.
4. **Missing Transaction Rollback on Generic Errors:** Several router endpoints catch `IntegrityError` but do not catch generic exceptions with rollbacks.
5. **Hardcoded Legacy Migration Data:** Migration `9a0b9ad7329b` contains hardcoded student IDs `(3, 7, 8, 10, 11)` and fixed course/department IDs.
6. **Frontend Type Incompatibility:** Frontend `Student` interface has 3 fields while backend model has 12 fields.

---

## SECTION 19 — CURRENT SYSTEM ARCHITECTURE DIAGRAM

```mermaid
flowchart TD
    subgraph Client ["Frontend (React 19 + TypeScript)"]
        UI_Home["HomePage.tsx"]
        UI_Students["StudentsPage.tsx (Legacy Incompatible)"]
        AxiosClient["client.ts (No Auth Token)"]
    end

    subgraph API ["FastAPI Backend (app.main:app)"]
        Router_Auth["/api/v1/auth (auth.py)"]
        Router_Users["/api/v1/users (users.py)"]
        Router_Dept["/api/v1/departments (departments.py)"]
        Router_Courses["/api/v1/courses (courses.py)"]
        Router_Faculty["/api/v1/faculty (faculty.py)"]
        Router_Students["/api/v1/students (students.py)"]
        Router_Subjects["/api/v1/subjects (subjects.py)"]
        Router_Enroll["/api/v1/enrollments (enrollments.py)"]
        Router_Att["/api/v1/attendance (attendance.py)"]
        Router_Assess["/api/v1/assessments (assessments.py)"]
        Router_Results["/api/v1/results (results.py)"]
        
        Service_Result["result_service.py (Active)"]
        Service_Feature["feature_service.py (Orphaned / Incompatible)"]
    end

    subgraph DB ["PostgreSQL Database"]
        T_Users[(users)]
        T_Dept[(departments)]
        T_Courses[(courses)]
        T_Faculty[(faculty)]
        T_Students[(students)]
        T_Subjects[(subjects)]
        T_Enroll[(enrollments)]
        T_Att[(attendance)]
        T_Assess[(assessments)]
    end

    subgraph Missing ["MISSING COMPONENTS"]
        M_MLModels["vcis_models/*.joblib (Not in repo)"]
        M_PredService["prediction_service.py"]
        M_PredRouter["/api/v1/predictions"]
        M_IntervRouter["/api/v1/interventions"]
        M_PredTable[(predictions table)]
        M_IntervTable[(interventions table)]
        M_Dashboards["Faculty/HOD/Student Dashboards"]
    end

    UI_Students --> AxiosClient
    AxiosClient -.->|401 Unauthorized| Router_Students
    
    Router_Auth --> T_Users
    Router_Students --> T_Students
    Router_Assess --> T_Assess
    Router_Att --> T_Att
    Router_Results --> Service_Result
    Service_Result --> T_Enroll
    Service_Result --> T_Subjects
    Service_Result --> T_Assess
    Service_Result --> T_Att
```

---

## SECTION 20 — CURRENT VS REQUIRED ARCHITECTURE COMPARISON

| Architectural Area | Current VCIS 3.0 State | Required Production VCIS 3.0 State | Gap Description & Action Required |
|---|---|---|---|
| **Database Schema** | 9 tables (Users to Assessments) | 11 tables (+ `predictions`, + `interventions`) | Create Alembic migration for predictions & interventions. |
| **Assessment Model** | AssessmentType (`INTERNAL`, `ASSIGNMENT`, `MIDTERM`, `FINAL`) | Explicit support for `CT1`, `CT2`, `ASSIGNMENT`, `FINAL` | Standardize `CT1` representation without fragile strings. |
| **ML Models** | Not in repository | 2 Joblib models in `vcis_models/` | Place `.joblib` files in repository root or backend directory. |
| **Feature Extraction** | Single-subject enrollment level in `feature_service.py` | Student + Semester level aggregation across all semester subjects | Rewrite `feature_service.py` to match exact feature signatures. |
| **Prediction Service** | None | `prediction_service.py` with singleton model loading & inference | Implement prediction service with rule-based risk classification. |
| **Prediction API** | None | `/api/v1/predictions` endpoints (single, semester batch) | Add prediction router. |
| **Intervention System** | None | `/api/v1/interventions` CRUD & workflow | Add intervention model, schema, service, and router. |
| **Frontend UI** | Bare skeleton (Home + broken Students page) | Role-based Dashboard (Student, Faculty, HOD, Admin) + Early Warning UI | Build modern dashboard, auth management, and ML prediction visualizer. |
| **Testing** | 0 tests | Comprehensive test suite for ML pipelines & API | Add pytest test suite. |

---

## SECTION 21 — ML FEATURE COMPATIBILITY AUDIT

### 21.1 Detailed Compatibility Matrix

#### Feature 1: `current_attendance`
- **Required By:** Model 1 (Sem 1) and Model 2 (Sem 2–4)
- **Current DB Source:** `attendance` table joined with `enrollments`
- **Current Service:** `result_service.get_enrollment_attendance` (Enrollment level)
- **Required Aggregation:** Aggregate all attendance records across all enrolled subjects for `student_id` in `current_semester`.
  $$\text{current\_attendance} = \frac{\sum \text{Present Sessions across all current subjects}}{\sum \text{Total Sessions across all current subjects}} \times 100$$
- **Compatible with Trained Model:** **PARTIAL** (Raw data exists; aggregation function must be updated to student-semester level).

#### Feature 2: `current_assignment_average`
- **Required By:** Model 1 (Sem 1) and Model 2 (Sem 2–4)
- **Current DB Source:** `assessments` table where `assessment_type = 'ASSIGNMENT'`
- **Current Service:** None (lumped in `feature_service`)
- **Required Aggregation:** Calculate percentage score for each assignment, then take arithmetic mean across all subjects in the current semester.
  $$\text{current\_assignment\_average} = \text{mean}\left(\frac{\text{obtained\_marks}}{\text{max\_marks}} \times 100\right) \quad \forall \text{ assignments in current semester}$$
- **Compatible with Trained Model:** **PARTIAL** (Data exists; filtering and aggregation logic must be written).

#### Feature 3: `current_ct1_average`
- **Required By:** Model 1 (Sem 1) and Model 2 (Sem 2–4)
- **Current DB Source:** `assessments` table
- **How CT1 is Identified:** Currently stored as `assessment_type = 'INTERNAL'` and `assessment_name` matching `"CT1"`
- **Required Aggregation:** Calculate CT1 percentage for each subject, then take arithmetic mean across all subjects in current semester.
  $$\text{current\_ct1\_average} = \text{mean}\left(\frac{\text{obtained\_marks}}{\text{max\_marks}} \times 100\right) \quad \forall \text{ CT1 tests in current semester}$$
- **Compatible with Trained Model:** **PARTIAL** (Requires standardized querying of CT1 assessments).

#### Feature 4: `previous_semester_score`
- **Required By:** Model 2 (Sem 2–4 Only)
- **Current DB Source:** `assessments` and `subjects` from `current_semester - 1`
- **Current Calculation:** `result_service.get_student_semester_result(student_id, current_semester - 1)['overall_percentage']`
- **Compatible with Trained Model:** **YES** (Logic exists in `result_service`; must be piped into feature extractor).

#### Feature 5: `previous_semester_attendance`
- **Required By:** Model 2 (Sem 2–4 Only)
- **Current DB Source:** `attendance` records for enrollments in `current_semester - 1`
- **Current Calculation:** Can be calculated by aggregating attendance across all enrollments in `current_semester - 1`.
- **Compatible with Trained Model:** **YES** (Query available; needs helper function in feature service).

### 21.2 Critical ML Rule Verification Checklist

| Critical Rule | Audit Status | Evidence / Verification |
|---|---|---|
| **CT2 Excluded from Predictions?** | **CRITICAL RISK IN CURRENT CODE** | `feature_service.py` currently sums all assessments blindly. Must be rewritten to explicitly exclude CT2. |
| **Final Result Excluded from Predictions?** | **CRITICAL RISK IN CURRENT CODE** | `feature_service.py` currently sums final assessments. Must be rewritten to exclude final exam marks. |
| **Student ID Excluded from Feature Vector?** | **SAFE** | `student_id` is an entity key and will only be used for query routing, not passed to `model.predict()`. |
| **Subject-Level Aggregated to Student-Semester?** | **REQUIRES REFACTORING** | Current code aggregates at enrollment level. Must aggregate across all semester subjects. |
| **Semester 1 Handled Without Artificial History?** | **SAFE** | Model 1 uses only 3 features and makes zero reference to previous semester. |

---

## SECTION 22 — DATA LEAKAGE AUDIT

| Potential Leakage Vector | Classification | Mechanism in Current Code | Prevention Strategy |
|---|---|---|---|
| **Final Exam Marks in Early Prediction** | **CRITICAL** | `feature_service.py` sums `Assessment.obtained_marks` across all records including `AssessmentType.FINAL`. | Filter queries strictly by `AssessmentType.ASSIGNMENT` and `AssessmentType.INTERNAL` (CT1 only). |
| **CT2 Assessment Marks in Early Prediction** | **HIGH** | `feature_service.py` does not filter out CT2 assessments. | Explicitly exclude assessments matching CT2 or occurring post-intervention cutoff. |
| **Future Attendance Records** | **MEDIUM** | If prediction is re-run late in semester, attendance percentage includes post-CT1 attendance. | Optional prediction date cutoff or milestone snapshotting. |
| **Current Semester Result Contamination** | **CRITICAL** | Using `StudentSemesterResultResponse.overall_percentage` as a feature for current semester. | Current semester overall percentage is strictly the TARGET outcome, never an input. |
| **Artificial Imputation in Semester 1** | **HIGH** | Imputing 0 or mean for `previous_semester_score` in Sem 1. | Strictly route Semester 1 to Model 1 (which requires no previous semester features). |

---

## SECTION 23 — DATABASE ↔ ML MAPPING

```
1. Feature: current_attendance (Float: 0.0 - 100.0)
   Database: attendance.status
   Query:
     SELECT 
       COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END)::FLOAT / COUNT(*)::FLOAT * 100.0
     FROM attendance a
     JOIN enrollments e ON a.enrollment_id = e.id
     JOIN subjects s ON e.subject_id = s.id
     WHERE e.student_id = :student_id AND s.semester = :current_semester;

2. Feature: current_assignment_average (Float: 0.0 - 100.0)
   Database: assessments.obtained_marks, assessments.max_marks, assessments.assessment_type
   Query:
     SELECT 
       AVG((ass.obtained_marks::FLOAT / ass.max_marks::FLOAT) * 100.0)
     FROM assessments ass
     JOIN enrollments e ON ass.enrollment_id = e.id
     JOIN subjects s ON e.subject_id = s.id
     WHERE e.student_id = :student_id 
       AND s.semester = :current_semester
       AND ass.assessment_type = 'ASSIGNMENT';

3. Feature: current_ct1_average (Float: 0.0 - 100.0)
   Database: assessments.obtained_marks, assessments.max_marks, assessments.assessment_type, assessments.assessment_name
   Query:
     SELECT 
       AVG((ass.obtained_marks::FLOAT / ass.max_marks::FLOAT) * 100.0)
     FROM assessments ass
     JOIN enrollments e ON ass.enrollment_id = e.id
     JOIN subjects s ON e.subject_id = s.id
     WHERE e.student_id = :student_id 
       AND s.semester = :current_semester
       AND ass.assessment_type = 'INTERNAL'
       AND (ass.assessment_name ILIKE '%CT1%' OR ass.assessment_name ILIKE '%CT-1%' OR ass.assessment_name ILIKE '%Class Test 1%');

4. Feature: previous_semester_score (Float: 0.0 - 100.0) [Semesters 2-4 Only]
   Database: assessments.obtained_marks, assessments.max_marks
   Query:
     Computed via result_service.get_student_semester_result(student_id, current_semester - 1)['overall_percentage']

5. Feature: previous_semester_attendance (Float: 0.0 - 100.0) [Semesters 2-4 Only]
   Database: attendance.status
   Query:
     Aggregated attendance percentage across all enrollments where s.semester = :current_semester - 1
```

---

## SECTION 24 — RECOMMENDED MODIFICATION PLAN

### Phase 1: Environment & Dependency Alignment
- Add `joblib`, `scikit-learn`, `pandas`, and `numpy` to `backend/requirements.txt`.
- Remove accidental `backend/package.json`.
- Fix duplicate `updated_at` attribute in `app/models/user.py`.
- Fix duplicate imports in `app/routers/results.py`.

### Phase 2: Database Schema Expansion (Migrations)
- Create new Alembic migration:
  - Create `predictions` table.
  - Create `interventions` table.
  - Create foreign keys and indexes.

### Phase 3: Core ML & Feature Engineering Pipeline
- Create directory `vcis_models/` and place `vcis_model_semester1.joblib` and `vcis_model_semesters2_4.joblib`.
- Refactor `backend/app/services/feature_service.py` to implement:
  - `get_student_semester_early_features(db, student_id, semester)`
  - Standardized aggregation for attendance, assignment avg, and CT1 avg.
  - Previous semester metrics extraction for Semesters 2–4.
  - Strict exclusion of CT2 and Final exam marks.
- Implement `backend/app/services/prediction_service.py`:
  - Startup model cache (singleton loader).
  - Feature extraction routing (Sem 1 -> Model 1, Sem 2–4 -> Model 2).
  - Inference calculation and risk level assignment (`HIGH_RISK`, `MEDIUM`, `LOW`).
  - Result persistence into `predictions` table.

### Phase 4: API Layer Expansion
- Create `backend/app/schemas/prediction.py` and `backend/app/schemas/intervention.py`.
- Create `backend/app/routers/predictions.py` (`POST /student/{id}`, `GET /student/{id}/latest`, `GET /semester/{sem}`).
- Create `backend/app/routers/interventions.py` (CRUD for faculty intervention management).
- Register new routers in `backend/app/main.py`.

### Phase 5: Security & Authorization Hardening
- Restrict `POST /api/v1/users/` to `ADMIN` role or implement closed self-registration.
- Resolve IDOR risks in student and result endpoints by adding role/ownership checks.

### Phase 6: Frontend Overhaul
- Implement Axios request interceptor in `frontend/src/api/client.ts` to attach `Authorization: Bearer <token>`.
- Build Login page and JWT state management.
- Build Academic Intelligence Dashboard:
  - Student Early Warning View (predicted score, risk badge, feature drivers).
  - Faculty Intervention Management View (assigning extra classes, counselling).
  - Update `StudentsPage.tsx` to match complete 12-field student schema.

### Phase 7: Verification & Testing
- Write unit tests in `tests/test_features.py` to verify mathematical accuracy and leak prevention.
- Write API integration tests in `tests/test_predictions_api.py`.
- Perform end-to-end flow test from attendance/CT1 entry -> prediction -> intervention -> resolution.

---

## SECTION 25 — FILE-BY-FILE CHANGE MAP

| File Path | Action | Rationale | Dependency / Priority |
|---|---|---|---|
| `backend/requirements.txt` | **MODIFY** | Add `joblib`, `scikit-learn`, `pandas`, `numpy` | Phase 1 / **BLOCKER** |
| `backend/package.json` | **DELETE** | Accidental npm file in backend | Phase 1 / Low |
| `backend/app/models/user.py` | **MODIFY** | Remove duplicate `updated_at` column | Phase 1 / Low |
| `backend/app/routers/results.py` | **MODIFY** | Clean up duplicate imports | Phase 1 / Low |
| `backend/alembic/versions/<new_rev>.py` | **ADD** | Migration creating `predictions` & `interventions` tables | Phase 2 / **HIGH** |
| `backend/app/models/prediction.py` | **ADD** | ORM Model for prediction history | Phase 2 / **HIGH** |
| `backend/app/models/intervention.py` | **ADD** | ORM Model for faculty interventions | Phase 2 / **HIGH** |
| `vcis_models/*.joblib` | **ADD** | Store pre-trained Colab regression models | Phase 3 / **BLOCKER** |
| `backend/app/services/feature_service.py` | **MODIFY** | Rewrite to student-semester level; exclude CT2/Final | Phase 3 / **BLOCKER** |
| `backend/app/services/prediction_service.py` | **ADD** | Model loading, feature vector construction, inference | Phase 3 / **BLOCKER** |
| `backend/app/schemas/prediction.py` | **ADD** | Pydantic DTOs for predictions | Phase 4 / **HIGH** |
| `backend/app/schemas/intervention.py` | **ADD** | Pydantic DTOs for interventions | Phase 4 / **HIGH** |
| `backend/app/routers/predictions.py` | **ADD** | REST endpoints for ML predictions | Phase 4 / **HIGH** |
| `backend/app/routers/interventions.py` | **ADD** | REST endpoints for intervention workflow | Phase 4 / **HIGH** |
| `backend/app/main.py` | **MODIFY** | Include prediction and intervention routers | Phase 4 / **HIGH** |
| `backend/app/routers/users.py` | **MODIFY** | Secure `POST /` with `require_roles(ADMIN)` | Phase 5 / Medium |
| `frontend/src/api/client.ts` | **MODIFY** | Add JWT Authorization header interceptor | Phase 6 / **BLOCKER** |
| `frontend/src/api/students.ts` | **MODIFY** | Align TypeScript types with backend `StudentCreate`/`Update` | Phase 6 / **HIGH** |
| `frontend/src/pages/students/StudentsPage.tsx` | **MODIFY** | Expand form fields for complete student record | Phase 6 / **HIGH** |
| `frontend/src/pages/LoginPage.tsx` | **ADD** | User login screen | Phase 6 / **HIGH** |
| `frontend/src/pages/DashboardPage.tsx` | **ADD** | Campus intelligence & early warning dashboard | Phase 6 / **HIGH** |
| `tests/test_feature_pipeline.py` | **ADD** | Unit tests for feature extraction and leak prevention | Phase 7 / Medium |

---

## SECTION 26 — CRITICAL ISSUES

### 1. Blockers (Must resolve before any ML prediction works)
- **ML Dependencies Missing:** `scikit-learn`, `joblib`, `pandas`, `numpy` are not in `backend/requirements.txt`.
- **Model Files Absent from Repo:** The `.joblib` files must be placed in a known location (`vcis_models/`).
- **Feature Extraction Incompatibility:** `feature_service.py` currently extracts subject-level data and lumps final exam marks into percentages. It must be rewritten to aggregate at the student-semester level.
- **Frontend Auth Disconnect:** `frontend/src/api/client.ts` does not attach bearer tokens, causing all authenticated API calls to fail.

### 2. High Priority
- **No Database Persistence for Predictions & Interventions:** Predictions are currently ephemeral without dedicated tables.
- **Unstructured CT1 Identification:** CT1 is identified via fragile text matching in `assessment_name`.
- **Frontend Student CRUD Broken:** Incompatible DTO payload between frontend form and backend schema.

### 3. Medium Priority
- **Unprotected User Registration:** `POST /api/v1/users/` allows public registration with `admin` role.
- **IDOR on Student & Result Endpoints:** Non-admin users can access any student's data by guessing IDs.
- **Zero Test Coverage:** No automated tests exist in the project.

### 4. Low Priority
- Duplicate column definition in `User` model.
- Duplicate imports in `results.py` router.
- Accidental `package.json` in `backend/`.

---

## SECTION 27 — WHAT IS ALREADY WORKING (DO NOT REWRITE)

The following modules and architectures are structurally sound, well-tested, and should **NOT** be rewritten:
1. **Core Database Engine & Session Management:** `backend/app/database.py` and `app/base.py` work cleanly with SQLAlchemy 2.0 and PostgreSQL.
2. **Authentication Security Core:** Password hashing with Argon2 (`app/core/security.py`) and JWT token parsing/verification (`app/core/dependencies.py` and `app/core/authorization.py`) are robust.
3. **Academic Catalog & Enrollment Management:** CRUD routers and models for `Departments`, `Courses`, `Subjects`, `Faculty`, and `Enrollments` are complete with strong relational integrity constraints.
4. **Attendance System:** `backend/app/models/attendance.py`, schemas, and router handle session-level attendance correctly with duplicate prevention constraints.
5. **Assessment Recording:** `backend/app/models/assessment.py` and router handle max/obtained marks validation and unique constraints per enrollment.
6. **Academic Result Service Core:** `backend/app/services/result_service.py` accurately computes semester credits, GPA, and subject overall percentages.

---

## SECTION 28 — UNKNOWN / NEEDS RUNTIME VERIFICATION

| Verification Item | Why Unknown via Static Audit | Runtime Action Required |
|---|---|---|
| **Live Database Connectivity** | PostgreSQL credentials in `.env` depend on local service state | Run `python backend/app/test_db.py` to confirm database is listening on port 5432. |
| **Current Alembic Revision in Live DB** | `alembic_version` table is stored inside PostgreSQL | Execute `alembic current` inside `backend/` to verify current head matches `5ef3d75a843a`. |
| **Integrity of Trained Joblib Artifacts** | Artifacts are stored outside repository | Inspect `.joblib` files with `joblib.load()` to verify feature list matches `['current_attendance', 'current_assignment_average', 'current_ct1_average']`. |
| **Real vs Synthetic Student Data** | Database rows are not committed in git | Check `SELECT COUNT(*) FROM students` to inspect existing database records. |

---

## SECTION 29 — FINAL EXECUTIVE SUMMARY

### 1. What VCIS 3.0 Currently Contains
VCIS 3.0 is a structured FastAPI + PostgreSQL + React 19 application providing full relational data storage and REST APIs for students, faculty, departments, courses, subjects, enrollments, attendance, and assessments.

### 2. What is Already Functional
The backend relational data model, authentication/JWT system, session management, enrollment integrity rules, attendance marking, assessment grade entry, and post-semester result aggregation are complete and functional.

### 3. What is Missing
The ML prediction pipeline, model loading singleton, student-semester feature aggregator, prediction persistence table, intervention workflow table, and frontend analytics dashboard are missing.

### 4. What Conflicts with the Trained ML Models
The existing `feature_service.py` computes metrics at the individual subject level instead of the student-semester level and aggregates all assessment marks together (causing severe final-exam and CT2 data leakage).

### 5. What Should Be Changed
- Add ML dependencies to `requirements.txt`.
- Rewrite `feature_service.py` to produce student-semester aggregated vectors (`current_attendance`, `current_assignment_average`, `current_ct1_average`, `previous_semester_score`, `previous_semester_attendance`).
- Add `prediction_service.py` and new migrations for `predictions` and `interventions`.
- Add Axios token interceptor and modern dashboard UI in the frontend.

### 6. What Should NOT Be Changed
Do not redesign the database schema for departments, courses, faculty, students, subjects, enrollments, attendance, or assessments. Do not replace SQLAlchemy 2.0, FastAPI, or React 19.

### 7. Safest Implementation Order
1. **Dependencies & Models:** Add ML packages -> Place `.joblib` files -> Add `predictions`/`interventions` migrations.
2. **Feature & Prediction Backend:** Rewrite `feature_service.py` -> Create `prediction_service.py` -> Create `predictions.py` and `interventions.py` routers.
3. **Security Hardening:** Attach JWT interceptor in frontend -> Add IDOR checks in backend.
4. **Frontend Dashboard:** Connect React dashboard to prediction and intervention APIs.
5. **Verification:** Run unit and integration tests to guarantee zero data leakage.

---
*Report generated strictly via static & structural audit of the VCIS 3.0 codebase.*
