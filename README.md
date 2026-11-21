# Enterprise HR Management System & AI Copilot

A full-stack, enterprise-grade HR Management System powered by **FastAPI**, **React (Vite)**, **PostgreSQL**, **LangGraph**, **FastMCP**, **Pinecone Vector Search (RAG)**, and **Groq (Qwen)**.

---

## Features

- **Role-Based Access Control (RBAC)**: Distinct permissions for `Admin`, `HR Staff`, `Manager`, and `Employee`.
- **AI Assistant Copilot**:
  - Context-aware natural language assistant orchestrated via **LangGraph**.
  - Document retrieval via **Pinecone Vector Search** with inline policy citations.
  - Autonomous tool invocation via **FastMCP** for leave balances, employee profiles, and pending approvals.
  - Strict data privacy restrictions preventing non-manager employees from accessing colleagues' private records.
- **Leave Management**:
  - Check Casual & Sick leave quotas.
  - Submit leave applications.
  - Dedicated **Manager Approval Console** with one-click approve/reject actions.
  - Strict `DD/MM/YYYY` date formatting across all operational tables.
- **HR Policy Documents (RAG Ingestion)**:
  - Upload DOCX/PDF company manuals, guidelines, and holiday calendars.
  - Chunks, embeds (SentenceTransformers), and indexes policy documents into Pinecone vector storage.
  - Admin controls for policy metadata inspection and removal.
- **Security & Compliance Audit Trail**:
  - Immutable operational logging in PostgreSQL for logins, leave requests, reviews, and AI tool executions.
  - Restricted strictly to HR Staff, Managers, and Admins.
- **Bcrypt Password Security**:
  - All employee credentials hashed and verified using salted `bcrypt`.

---

## Architecture

```
                    ┌────────────────────────────────────────┐
                    │      React Frontend (Vite + TS)        │
                    │   Admin Theme • Dashboard • Copilot    │
                    └───────────────────┬────────────────────┘
                                        │ REST APIs
                                        ▼
                    ┌────────────────────────────────────────┐
                    │         FastAPI Backend (Python)       │
                    │ Auth • Leaves • Documents • Audit Logs │
                    └───────┬────────────────────────┬───────┘
                            │                        │
               Tool Calls   │                        │ SQLAlchemy ORM
                            ▼                        ▼
        ┌─────────────────────────────┐   ┌───────────────────────┐
        │     LangGraph Orchestrator  │   │  PostgreSQL Database  │
        │  • Groq (Qwen LLM)          │   │  • employees (bcrypt) │
        │  • FastMCP Tools            │   │  • leave_balances     │
        │  • Pinecone Vector Search   │   │  • leave_requests     │
        └─────────────────────────────┘   │  • hr_documents       │
                                          │  • audit_events       │
                                          └───────────────────────┘
```

---

## Project Structure

```
├── backend/
│   ├── core/               # DB connection, configuration, bcrypt security
│   ├── documents/          # Uploaded policy documents directory
│   ├── models/             # SQLAlchemy ORM models (Employees, Leaves, Audits, Docs)
│   ├── repository/         # Data access layers
│   ├── routers/            # FastAPI API endpoints (Auth, Leaves, Chat, Admin)
│   ├── schemas/            # Pydantic validation schemas
│   ├── services/           # Business logic, RAG ingestion, LangGraph workflow
│   ├── sql/                # PostgreSQL DDL schema and seed data
│   ├── main.py             # FastAPI entrypoint
│   ├── mcp_server.py       # FastMCP tools for AI assistant
│   ├── migrate_passwords.py# Bcrypt migration script
│   ├── requirements.txt    # Python backend dependencies
│   ├── test_app.py         # Pytest automated test suite
│   └── .env.example        # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── api.ts          # Backend API client
│   │   ├── App.tsx         # Main application component & tab routing
│   │   ├── App.css         # Admin styling & responsive layout
│   │   └── main.tsx        # React root mount
│   ├── package.json        # Frontend dependencies
│   └── vite.config.ts      # Vite configuration
└── README.md
```

---

## Getting Started

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 14+
- Pinecone Account & API Key
- Groq Cloud API Key

### 2. Database Setup
1. Create a PostgreSQL database named `hr_assistant`:
   ```sql
   CREATE DATABASE hr_assistant;
   ```
2. Execute the schema and seed files located in `backend/sql/`:
   ```bash
   psql -U postgres -d hr_assistant -f backend/sql/schema.sql
   psql -U postgres -d hr_assistant -f backend/sql/seed.sql
   ```

### 3. Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your PostgreSQL connection string, Pinecone API key, and Groq API key.
5. Migrate employee passwords to bcrypt:
   ```bash
   python migrate_passwords.py
   ```
6. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### 4. Frontend Setup
1. In a new terminal, navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
4. Access the web application at `http://localhost:5173`.

---

## Default Test Accounts

All accounts use password: `password123` (hashed via bcrypt in the database).

| Role | Name | Email |
|------|------|-------|
| **Admin** | Admin User | `admin@company.com` |
| **HR Staff** | Priya Sharma | `priya@company.com` |
| **Manager (IT)** | Sanjay Kumar | `sanjay@company.com` |
| **Employee (IT)** | Arun Kumar | `arun@company.com` |

---

## Running Automated Tests

Run the test suite using `pytest`:
```bash
pytest backend/test_app.py -v
```
Tests validate:
- Authentication & bcrypt password verification
- Role-based access control (RBAC) on leave approvals
- Document ingestion & embedding into Pinecone
- LangGraph assistant policy citations and employee privacy restrictions
