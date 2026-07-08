# EduCore Platform

<div align="center">

# 🎓 EduCore

### Modern Education Platform Built for the Future

*A scalable digital learning ecosystem designed to provide curriculum-based educational resources, premium learning materials, AI-powered learning tools, and school management solutions.*

---

![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?style=for-the-badge&logo=typescript)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?style=for-the-badge&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)
![Redis](https://img.shields.io/badge/Redis-7-red?style=for-the-badge&logo=redis)

</div>

---

# Table of Contents

- Overview
- Vision
- Features
- Technology Stack
- Architecture
- Project Structure
- Backend Architecture
- Frontend Architecture
- Database Design
- API Design
- Security
- Performance
- Installation
- Environment Variables
- Deployment
- Roadmap
- Contributing
- License

---

# Overview

EduCore is an enterprise-grade education platform that enables students, teachers, parents, schools, and institutions to access structured curriculum-based learning resources through a modern cloud platform.

The platform starts with Kenya's CBC curriculum but has been architected to support multiple international curricula including:

- CBC (Kenya)
- Cambridge
- British Curriculum
- American Curriculum
- IB
- African National Curricula
- University Content

EduCore follows a modular architecture allowing future expansion into AI tutoring, adaptive learning, mobile applications, analytics, and digital classrooms.

---

# Vision

To become the world's leading digital education ecosystem by providing:

- High-quality educational content
- Affordable learning resources
- Curriculum-based learning
- AI-assisted education
- Global accessibility
- School digitization
- Personalized learning

---

# Core Features

## Learning Resources

- Revision Papers
- Worksheets
- Lesson Notes
- Mock Exams
- Past Papers
- Marking Schemes
- Lesson Plans
- Schemes of Work
- Topic Quizzes
- Assignments

---

## Smart Search

- Search by Grade
- Subject
- Topic
- Term
- Year
- Resource Type
- Difficulty
- Keywords

---

## Premium Features

- Premium Downloads
- Unlimited Access
- Subscription Plans
- M-Pesa Payments
- Future Stripe Integration

---

## User System

- Students
- Teachers
- Parents
- Schools
- Administrators

---

## Dashboard

- Saved Resources
- Download History
- Purchases
- Analytics
- Notifications
- Settings

---

## Admin Dashboard

- Resource Management
- User Management
- Payments
- Analytics
- Reviews
- Reports
- Schools
- AI Monitoring

---

# Technology Stack

## Frontend

- Next.js 15
- TypeScript
- React 19
- Tailwind CSS
- Zustand
- React Query
- Axios
- React Hook Form
- Zod

---

## Backend

- FastAPI
- SQLAlchemy 2.0
- Pydantic v2
- Alembic
- AsyncPG
- JWT Authentication
- OAuth2
- Redis

---

## Database

- PostgreSQL 16

---

## Storage

- Cloudflare R2
- AWS S3 Compatible

---

## Payments

- Safaricom Daraja API
- M-Pesa STK Push

---

## Infrastructure

- Docker
- Docker Compose
- Nginx
- GitHub Actions
- Terraform
- Kubernetes (Future)

---

# System Architecture

```
                        Users
                          │
            ┌─────────────┼─────────────┐
            │             │             │
         Web App      Mobile App     Admin
            │             │             │
            └─────────────┼─────────────┘
                          │
                     FastAPI API
                          │
      ┌───────────────────┼───────────────────┐
      │                   │                   │
 Authentication      Business Logic      Background Jobs
      │                   │                   │
      └───────────────────┼───────────────────┘
                          │
                  Repository Layer
                          │
                     PostgreSQL
                          │
      ┌───────────────────┼───────────────────┐
      │                   │                   │
     Redis          Cloudflare R2         M-Pesa
```

---

# Complete Project Structure

```text
educore-platform/
│
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── .gitignore
├── .editorconfig
├── .prettierrc
├── docker-compose.yml
├── Makefile
├── .env.example
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── middleware.ts
│   ├── tailwind.config.ts
│   ├── eslint.config.js
│   ├── public/
│   │   ├── logos/
│   │   ├── icons/
│   │   ├── images/
│   │   ├── assets/
│   │   ├── robots.txt
│   │   ├── sitemap.xml
│   │   └── favicon.ico
│   │
│   └── src/
│       ├── app/
│       │   ├── (public)/
│       │   ├── (auth)/
│       │   ├── (dashboard)/
│       │   ├── admin/
│       │   ├── grades/
│       │   ├── subjects/
│       │   ├── topics/
│       │   ├── resources/
│       │   ├── exams/
│       │   ├── worksheets/
│       │   ├── notes/
│       │   ├── quizzes/
│       │   ├── downloads/
│       │   ├── premium/
│       │   ├── checkout/
│       │   ├── pricing/
│       │   ├── search/
│       │   ├── reviews/
│       │   ├── notifications/
│       │   ├── settings/
│       │   ├── api/
│       │   ├── globals.css
│       │   ├── layout.tsx
│       │   └── page.tsx
│       │
│       ├── components/
│       ├── services/
│       ├── hooks/
│       ├── store/
│       ├── providers/
│       ├── context/
│       ├── lib/
│       ├── utils/
│       ├── constants/
│       ├── config/
│       ├── assets/
│       └── types/
│
├── backend/
│   │
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── .env.example
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── app/
│   │   │
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   ├── router.py
│   │   │   │
│   │   │   └── v1/
│   │   │       ├── auth/
│   │   │       ├── users/
│   │   │       ├── grades/
│   │   │       ├── subjects/
│   │   │       ├── topics/
│   │   │       ├── resources/
│   │   │       ├── notes/
│   │   │       ├── worksheets/
│   │   │       ├── exams/
│   │   │       ├── quizzes/
│   │   │       ├── downloads/
│   │   │       ├── search/
│   │   │       ├── reviews/
│   │   │       ├── payments/
│   │   │       ├── subscriptions/
│   │   │       ├── notifications/
│   │   │       ├── analytics/
│   │   │       ├── schools/
│   │   │       ├── teachers/
│   │   │       ├── students/
│   │   │       ├── ai/
│   │   │       └── admin/
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   ├── logging.py
│   │   │   ├── exceptions.py
│   │   │   ├── middleware.py
│   │   │   └── lifespan.py
│   │   │
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   ├── base.py
│   │   │   └── migrations/
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── dependencies/
│   │   ├── permissions/
│   │   ├── validators/
│   │   ├── middleware/
│   │   ├── storage/
│   │   ├── cache/
│   │   ├── tasks/
│   │   ├── workers/
│   │   ├── integrations/
│   │   │   ├── mpesa/
│   │   │   ├── email/
│   │   │   ├── sms/
│   │   │   ├── whatsapp/
│   │   │   └── storage/
│   │   │
│   │   ├── templates/
│   │   └── utils/
│   │
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
│
├── mobile/
│   └── educore-mobile/
│
├── infrastructure/
│   ├── docker/
│   ├── nginx/
│   ├── github-actions/
│   ├── terraform/
│   └── kubernetes/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── deployment/
│   ├── database/
│   ├── security/
│   ├── payments/
│   ├── ai/
│   └── mobile/
│
├── scripts/
│   ├── deploy.sh
│   ├── backup.sh
│   ├── restore.sh
│   ├── create_admin.py
│   ├── seed_database.py
│   └── generate_demo_content.py
│
└── assets/
    ├── branding/
    ├── mockups/
    └── design-system/
```

---

# Security

- JWT Authentication
- Refresh Tokens
- Role-Based Access Control (RBAC)
- Password Hashing (Argon2/Bcrypt)
- HTTPS Enforcement
- Rate Limiting
- CORS Protection
- SQL Injection Protection
- XSS Protection
- Secure File Storage
- Audit Logging

---

# Performance

- Async FastAPI
- Redis Caching
- PostgreSQL Indexing
- Background Workers
- Cloudflare CDN
- Pagination
- Connection Pooling
- Lazy Loading
- GZip/Brotli Compression

---

# Installation

## Clone

```bash
git clone https://github.com/your-org/educore-platform.git

cd educore-platform
```

## Frontend

```bash
cd frontend

npm install

npm run dev
```

## Backend

```bash
cd backend

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

alembic upgrade head

uvicorn app.main:app --reload
```

---

# Environment Variables

```env
APP_NAME=EduCore

APP_ENV=development

SECRET_KEY=

DATABASE_URL=

REDIS_URL=

JWT_SECRET_KEY=

JWT_REFRESH_SECRET=

CLOUDFLARE_ENDPOINT=

CLOUDFLARE_ACCESS_KEY=

CLOUDFLARE_SECRET_KEY=

EMAIL_API_KEY=

MPESA_CONSUMER_KEY=

MPESA_CONSUMER_SECRET=
```

---

# Future Roadmap

### Phase 1

- Core Infrastructure
- Authentication
- User Management

### Phase 2

- Grades
- Subjects
- Topics
- Resources

### Phase 3

- PDF Storage
- Search
- Downloads

### Phase 4

- Premium Content
- M-Pesa
- Subscriptions

### Phase 5

- Analytics
- Notifications
- Reviews

### Phase 6

- School Management

### Phase 7

- AI Tutor

### Phase 8

- Mobile Applications

### Phase 9

- International Curricula

---

# License

Private Commercial License

---

# EduCore Mission

> **"Making quality education accessible, structured, secure, and scalable for every learner around the world."**
