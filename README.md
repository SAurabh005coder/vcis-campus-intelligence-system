# VCIS — Virtual Campus Intelligence System

VCIS is an AI-powered campus intelligence platform that combines academic management, predictive performance analytics, early machine learning predictions, and faculty/HOD intervention tracking.

---

## Architecture & Deployment Model

VCIS is architected as a decoupled client-server platform:

```
┌─────────────────────────┐          HTTPS / REST (JWT)          ┌─────────────────────────┐
│     VCIS Frontend       │ ────────────────────────────────────> │      VCIS Backend       │
│  (React + TypeScript)   │                                       │   (FastAPI + Python)    │
│    Hosted on Netlify    │ <──────────────────────────────────── │ Hosted on Python Server │
└─────────────────────────┘                                       └───────────┬─────────────┘
                                                                              │
                                                                   PostgreSQL │ ML Models
                                                                              ▼
                                                                 ┌──────────────────────────┐
                                                                 │ PostgreSQL Database      │
                                                                 │ vcis_models/*.joblib     │
                                                                 └──────────────────────────┘
```

### 1. Frontend (Netlify)
- **Stack**: React 18, TypeScript, Vite, Vanilla CSS Design System.
- **Hosting**: Netlify static site / SPA hosting.
- **Routing**: Single-Page Application (SPA) with rewrite rules (`/* -> /index.html`) configured via `netlify.toml` and `frontend/public/_redirects`.
- **Environment Configuration**: Set `VITE_API_BASE_URL` in Netlify Site Settings > Environment Variables to point to your live FastAPI backend domain (e.g. `https://api.yourdomain.com`).

> **Note**: Netlify hosts the frontend client only. Netlify does **not** run the FastAPI backend server or PostgreSQL database.

### 2. Backend (Python Hosting Service)
- **Stack**: FastAPI, SQLAlchemy, Alembic, Pydantic, Psycopg 3.
- **Hosting**: Independent Python container/host (e.g., Render, Railway, AWS ECS, Fly.io).
- **CORS Configuration**: Configure `ALLOWED_ORIGINS` in your backend environment to include your production Netlify domain (e.g., `ALLOWED_ORIGINS=https://your-site.netlify.app`).

### 3. Database
- **Engine**: PostgreSQL 15+.
- **Schema Management**: Managed via Alembic migrations (`alembic upgrade head`).
- **Connection**: Configured via `DATABASE_URL` environment variable.

### 4. Machine Learning Models
- **Trained Artifacts**: `vcis_models/vcis_model_semester1.joblib` and `vcis_models/vcis_model_semesters2_4.joblib`.
- **Runtime**: Evaluated on-demand by the backend `PredictionService`. Model files are committed in the repository so the backend container can load them directly.

---

## Local Development Setup

### Backend Setup
```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1    # Windows
source .venv/bin/activate       # Linux/macOS

# 2. Configure environment
cp backend/.env.example backend/.env

# 3. Start development server
cd backend
python -m uvicorn app.main:app --reload
```
API docs available at `http://127.0.0.1:8000/docs`.

### Frontend Setup
```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Configure environment
cp .env.example .env

# 3. Start development server
npm run dev
```
Application accessible at `http://localhost:5173`.

### Production Build Verification
From repository root:
```bash
npm --prefix frontend run build
```

---

## Test & Development Accounts

> [!WARNING]
> **DEVELOPMENT & TESTING ONLY:**
> The credentials below are strictly for local development and demonstration with seeded test databases.
> Never reuse these test credentials or placeholder secret keys in production.

| Role | Email ID | Password | Local Dashboard URL |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@example.com` | `AdminPassword123!` | `http://localhost:5173/admin` |
| **Faculty** | `faculty1@example.com` | `FacultyPassword123!` | `http://localhost:5173/faculty` |
| **HOD** | `hod1@example.com` | `HodPassword123!` | `http://localhost:5173/hod` |
| **Student** | `student1@example.com` | `TestPassword123!` | `http://localhost:5173/student` |