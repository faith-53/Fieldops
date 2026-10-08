FieldOps
=======

A full-stack field service management platform for
managing customers, technicians, service jobs,
expenses and operational reporting.

Architecture
------------

React → Nginx → Django REST API
                    │
             ┌──────┴──────┐
             ↓             ↓
        PostgreSQL       Redis
                           ↓
                         Celery

A job is not a CRUD record. It moves through an enforced workflow:

PENDING → ASSIGNED → ACCEPTED → IN_PROGRESS → COMPLETED → VERIFIED → CLOSED

Example rule: a technician cannot mark a job COMPLETED without a completion note.
Managers verify work, then close it. Every transition is written to JobUpdate.

Features
--------

✓ JWT authentication
✓ Role-based access control (ADMIN / MANAGER / TECHNICIAN)
✓ Job workflow management
✓ Rule-based technician assignment (skill, availability, workload, distance)
✓ Audit logging
✓ File uploads (before/after photos, receipts, documents)
✓ Background tasks (deadline and overdue alerts)
✓ Notifications
✓ Reporting
✓ CSV/PDF exports
✓ Dockerized development
✓ CI/CD (GitHub Actions + Trivy)
✓ AWS-ready (RDS, S3, ECS/EC2, HTTPS)

Quick start (Docker)
--------------------

cp .env.example .env
docker compose up --build

Open http://localhost

Demo accounts
-------------

Admin      admin@fieldops.local     / admin12345
Manager    manager@fieldops.local   / manager12345
Technician john@fieldops.local      / tech12345

Local development without Docker
--------------------------------

Backend (from backend/):

  python -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt
  set USE_SQLITE=true
  python manage.py migrate
  python manage.py seed_demo
  python manage.py runserver

Celery (optional, needs Redis):

  celery -A config worker -l info
  celery -A config beat -l info

Frontend (from frontend/):

  npm install
  npm run dev

API (examples)
--------------

POST /api/auth/login/
GET  /api/jobs/
POST /api/jobs/
GET  /api/jobs/1042/
POST /api/jobs/1042/assign/
GET  /api/jobs/1042/suggestions/
POST /api/jobs/1042/accept/
POST /api/jobs/1042/start/
POST /api/jobs/1042/complete/
POST /api/jobs/1042/verify/
POST /api/jobs/1042/close/
GET  /api/reports/jobs/
GET  /api/technicians/performance/

Permissions are enforced in Django, not by hiding buttons:

- ADMIN: users, jobs, customers, reports, everything
- MANAGER: customers, jobs, reports, technicians
- TECHNICIAN: own jobs, notes, expenses, uploads

Assignment scoring
------------------

score = skill_match + availability + workload + distance

The manager still chooses who to assign; FieldOps ranks candidates.

Production notes
----------------

- Set DJANGO_ENV=production and a real DJANGO_SECRET_KEY
- Point PostgreSQL at Amazon RDS
- Set USE_S3=true and an S3 bucket for uploads
- Run Gunicorn behind Nginx, terminate TLS at a load balancer or Nginx
- Run Celery worker + beat against ElastiCache Redis
- Deploy images from GHCR to ECS or EC2

Tests
-----

cd backend
pytest
