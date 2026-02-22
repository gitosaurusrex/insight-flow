# InsightFlow - AI-Powered Feedback & Analytics Platform

A production-style SaaS platform that collects user feedback, processes it through an AI pipeline (sentiment analysis, keyword extraction, embeddings), and presents analytics through a React dashboard.

## Architecture

```
                    ┌─────────────┐
                    │   Frontend  │
                    │  (React/    │
                    │   Vite)     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   API       │
                    │  (FastAPI)  │
                    └──┬────┬──┬──┘
                       │    │  │
            ┌──────────┘    │  └──────────┐
            │               │             │
    ┌───────▼───┐   ┌──────▼──────┐  ┌───▼────┐
    │ PostgreSQL │   │   MongoDB   │  │ Redis  │
    │ (metadata) │   │  (content)  │  │(cache/ │
    └────────────┘   └─────────────┘  │broker) │
                                      └───┬────┘
                                          │
                                   ┌──────▼──────┐
                                   │   Worker    │
                                   │  (Celery)   │
                                   │  AI Pipeline│
                                   └─────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy, Alembic |
| AI/ML | HuggingFace Transformers, sentence-transformers |
| Frontend | React 18, Vite, Chart.js |
| Databases | PostgreSQL 16, MongoDB 7 |
| Cache/Broker | Redis 7 |
| Workers | Celery |
| DevOps | Docker, GitHub Actions, Render |

## Local Setup

### Prerequisites
- Docker & Docker Compose
- Git

### Quick Start

```bash
# Clone the repository
git clone <repo-url> && cd insightflow

# Start all services
docker-compose up --build

# Services available at:
# Frontend: http://localhost:3000
# API:      http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Worker
celery -A app.tasks.celery_app worker --loglevel=info -B

# Frontend
cd frontend
npm install
npm run dev
```

## API Summary

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |

### Feedback
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/feedback` | Submit feedback |
| GET | `/api/feedback` | List feedback (paginated) |
| GET | `/api/feedback/{id}` | Get feedback detail |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/sentiment-trends` | Sentiment over time |
| GET | `/api/analytics/category-breakdown` | Category distribution |
| GET | `/api/analytics/volume-over-time` | Submission volume |

All feedback and analytics endpoints require JWT authentication via `Authorization: Bearer <token>` header.

## AI Pipeline

When feedback is submitted:
1. Metadata stored in PostgreSQL, raw text in MongoDB
2. Celery task enqueued for background processing
3. Text cleaning (HTML removal, normalization)
4. Sentiment analysis (DistilBERT fine-tuned on SST-2)
5. Keyword extraction (frequency-based)
6. Embedding generation (all-MiniLM-L6-v2)
7. Auto-categorization (bug, feature_request, praise, complaint, question, general)
8. Both databases updated, analytics cache invalidated

## Deployment (Render)

1. Push to GitHub
2. Connect repo to Render
3. Use `render.yaml` for Blueprint deployment
4. Configure MongoDB connection (external provider like MongoDB Atlas)
5. Set environment variables

## Scaling Considerations

- **API**: Horizontal scaling via Gunicorn workers + load balancer
- **Workers**: Scale Celery workers independently based on queue depth
- **PostgreSQL**: Connection pooling, read replicas for analytics queries
- **MongoDB**: Sharding on metadata_id for large datasets
- **Redis**: Cluster mode for high-availability caching
- **Frontend**: CDN deployment for static assets

## Testing

```bash
cd backend
pip install aiosqlite pytest-asyncio
pytest app/tests/ -v --cov=app
```

## Future Improvements

- Vector similarity search endpoint for semantic feedback search
- Rate limiting middleware
- Role-based access control (admin, analyst, viewer)
- Prometheus/Grafana observability
- Structured JSON logging
- WebSocket real-time dashboard updates
- Feedback export (CSV/PDF)
- Multi-language sentiment analysis
