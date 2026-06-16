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
