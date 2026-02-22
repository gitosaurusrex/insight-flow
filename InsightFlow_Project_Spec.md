# InsightFlow -- AI-Powered Feedback & Analytics Platform

## Project Overview

Build a production-style, containerized, deployable SaaS backend +
frontend system demonstrating:

-   Scalable Python backend architecture
-   RESTful APIs
-   Relational + NoSQL databases
-   Background workers and data pipelines
-   AI/ML integration
-   Docker containerization
-   CI/CD pipeline
-   Cloud deployment compatibility (Render)
-   React frontend

------------------------------------------------------------------------

# 1. Tech Stack

## Backend

-   Python 3.11+
-   FastAPI
-   SQLAlchemy
-   Alembic
-   PostgreSQL
-   MongoDB
-   Redis
-   Celery
-   JWT Authentication
-   Pydantic v2
-   Uvicorn + Gunicorn

## AI / ML

-   HuggingFace Transformers
-   sentence-transformers
-   scikit-learn (optional)

## Frontend

-   React
-   Vite
-   Axios
-   Chart.js

## DevOps

-   Docker
-   docker-compose
-   GitHub Actions
-   Render-compatible configuration

------------------------------------------------------------------------

# 2. High-Level Architecture

System components:

1.  API Service (FastAPI)
2.  Worker Service (Celery)
3.  PostgreSQL
4.  MongoDB
5.  Redis
6.  React frontend

Each must run in separate containers.

------------------------------------------------------------------------

# 3. Backend Architecture

Use layered structure:

backend/ app/ api/ core/ models/ schemas/ services/ repositories/ tasks/
tests/

Follow strict separation of concerns.

------------------------------------------------------------------------

# 4. Database Design

## PostgreSQL Tables

### users

-   id (UUID)
-   email
-   password_hash
-   created_at

### organizations

-   id (UUID)
-   name
-   owner_id (FK users)

### feedback_metadata

-   id (UUID)
-   org_id (FK organizations)
-   status
-   sentiment_score
-   category
-   created_at

Add indexes and foreign keys. Use Alembic for migrations.

## MongoDB Collection: feedback_content

Document structure:

{ metadata_id: UUID, raw_text: string, cleaned_text: string, embedding:
\[float\], keywords: \[string\], processed_at: datetime }

Add index on metadata_id.

------------------------------------------------------------------------

# 5. REST API Requirements

## Auth

-   POST /auth/register
-   POST /auth/login
-   JWT access tokens
-   bcrypt password hashing

## Feedback

-   POST /feedback
-   GET /feedback
-   GET /feedback/{id}

## Analytics

-   GET /analytics/sentiment-trends
-   GET /analytics/category-breakdown
-   GET /analytics/volume-over-time

Include pagination, filtering, proper status codes, validation, and
exception handling.

------------------------------------------------------------------------

# 6. AI / ML Pipeline

When feedback is submitted:

1.  Store metadata in PostgreSQL
2.  Store raw content in MongoDB
3.  Enqueue background task

Background task must: - Clean text - Run sentiment analysis - Extract
keywords - Generate embedding - Update PostgreSQL - Update MongoDB

Optional: daily anomaly detection job.

------------------------------------------------------------------------

# 7. Background Worker

-   Celery with Redis broker
-   Separate container
-   Retry logic
-   Logging
-   Idempotent tasks

Include scheduled daily aggregation job storing summary data.

------------------------------------------------------------------------

# 8. Caching

Use Redis to cache analytics endpoints (TTL 5 minutes). Invalidate cache
when new feedback is processed.

------------------------------------------------------------------------

# 9. Frontend Requirements

Pages: - Login/Register - Dashboard

Dashboard must include: - Feedback submission form - Sentiment trend
chart - Category breakdown chart - Feedback list with filters

Use Axios, JWT auth, Chart.js. Include loading states and error
handling.

------------------------------------------------------------------------

# 10. Performance

-   Async endpoints
-   DB indexing
-   Pagination limits
-   Gunicorn worker config
-   Basic Locust load test

Document performance considerations.

------------------------------------------------------------------------

# 11. Testing

-   pytest
-   Unit tests for services
-   API integration tests
-   Mock ML layer

Minimum 60% coverage.

------------------------------------------------------------------------

# 12. Docker

Create: - Dockerfile (API) - Dockerfile (Worker) - docker-compose.yml

Must start: - API - Worker - PostgreSQL - MongoDB - Redis - Frontend

------------------------------------------------------------------------

# 13. CI/CD

GitHub Actions:

On PR: - Install dependencies - Run lint - Run tests

On main: - Build Docker images

------------------------------------------------------------------------

# 14. Render Deployment

Include: - render.yaml - Separate web + worker services - Managed
PostgreSQL - Environment variable config

No hardcoded secrets.

------------------------------------------------------------------------

# 15. Documentation

README must include: 1. Architecture diagram 2. Tech stack explanation
3. Local setup instructions 4. Docker instructions 5. Deployment
instructions 6. API summary 7. Scaling considerations 8. Future
improvements

------------------------------------------------------------------------

# 16. Engineering Standards

-   Type hints everywhere
-   PEP8 compliance
-   Docstrings
-   Clear separation of concerns
-   Dependency injection
-   Explicit error handling

------------------------------------------------------------------------

# 17. Optional Advanced Features

-   Vector similarity search endpoint
-   Rate limiting middleware
-   Role-based access control
-   Observability metrics
-   Structured logging

------------------------------------------------------------------------

# 18. Success Criteria

Project must: - Run locally via docker-compose - Deploy to Render -
Support async background processing - Demonstrate relational + NoSQL DB
usage - Include caching, ML, CI, containerization - Follow
production-style architecture
