# Security Audit & Compliance Platform

A modern, secure web application designed to track assets, compliance frameworks (e.g., SOC 2, ISO 27001, OWASP ASVS), security controls, audits, and compliance findings.

This repository contains:
1. **Backend**: FastAPI app with SQLite database (SQLAlchemy), rate limiting, and standard security headers.
2. **Frontend**: React application built with Vite, utilizing Lucide React icons and Recharts for interactive analytics.

---

## Features

- **Compliance Framework Tracking**: Monitor compliance against frameworks such as SOC 2, ISO 27001, and OWASP ASVS.
- **Controls & Auditing**: Maintain a list of security controls, audit logs, and compliance statuses.
- **Asset Management**: Catalog systems, databases, and physical/logical resources.
- **Security Findings**: Track vulnerabilities, audits, and compliance gaps.
- **JWT-Based Authentication**: Secure login mechanism using hashed passwords (`bcrypt`) and JWT access tokens.
- **Built-in Security Headers**: Pre-configured secure HTTP headers (`X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy`, etc.).
- **API Rate Limiting**: Protection against brute-force attacks via built-in rate limiters.
- **Automatic Database Seeding**: Pre-loaded default security frameworks and automated generation of unique, secure initial admin credentials.

---

## Directory Structure

```text
├── backend/                  # Python FastAPI Backend
│   ├── app/                  # Application core, routers, models, schemas
│   ├── tests/                # Pytest suites
│   ├── Dockerfile            # Container definition for the backend
│   └── requirements.txt      # Python package dependencies
├── frontend/                 # React Frontend
│   ├── src/                  # React components, pages, styling
│   ├── Dockerfile            # Container definition for the frontend
│   └── package.json          # Node.js dependencies & scripts
├── docker-compose.yml        # Multi-container orchestrator configuration
├── .env.example              # Sample environment variables config
└── .gitignore                # Git exclusion rules
```

---

## Setup & Running Guide

### Option 1: Quickstart with Docker Compose (Recommended)

To run the entire stack (both frontend and backend) simultaneously:

1. Clone this repository to your local machine.
2. Make a copy of `.env.example` named `.env`:
   ```bash
   cp .env.example .env
   ```
3. Run the services using Docker Compose:
   ```bash
   docker-compose up --build
   ```
4. Access the applications:
   - **Frontend**: [http://localhost:3000](http://localhost:3000)
   - **Backend API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2: Local Manual Setup

#### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   
   # On Windows (Command Prompt)
   .venv\Scripts\activate
   # On Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   # On macOS/Linux
   source .venv/bin/activate
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the environment file. Create a `.env` file in the project root (`project1/.env`) using `.env.example` as a template:
   ```env
   ENV=dev
   DATABASE_URL=sqlite:///./compliance.db
   JWT_SECRET_KEY=dev_secret_key_change_me_in_production
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   CORS_ORIGINS=http://localhost:3000
   ```
5. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install the Node.js packages:
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```
4. Access the frontend at `http://localhost:3000`.

---

## Initial Credentials Setup

When the backend runs for the first time, it automatically creates the database schema and seeds default compliance frameworks. It also creates a temporary administrator account.

1. **Locate temporary admin password**:
   - Check the terminal output of the backend service on its first run, **OR**
   - Read the generated `backend/admin_setup.txt` file which is created in your workspace.
2. **Log in**:
   - Go to [http://localhost:3000/login](http://localhost:3000/login).
   - Use the username `admin` and the password from `admin_setup.txt`.
3. **Change Password**:
   - The platform will force a password reset upon the first successful login. Update your password to a strong, secure value.

> [!WARNING]
> Do not commit the generated `backend/admin_setup.txt` file or your local `.env` file to your Git repository. These are excluded by default in the project's `.gitignore` file.

---

## Running Tests

To run the backend test suite:

1. Navigate to the `backend` directory and activate the virtual environment.
2. Run `pytest`:
   ```bash
   pytest
   ```
