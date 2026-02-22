"""
Local development server that runs without Docker/PostgreSQL/MongoDB/Redis.
Uses SQLite + in-memory stores for quick local preview.
"""

import asyncio
import json
import uuid
import re
import random
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from pydantic_settings import BaseSettings
from sqlalchemy import String, Float, DateTime, ForeignKey, select, func, cast, Date, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ─── Config ───────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    SECRET_KEY: str = "local-dev-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

settings = Settings()

# ─── Database (SQLite) ────────────────────────────────────────────────────────

engine = create_async_engine("sqlite+aiosqlite:///./insightflow.db", echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class FeedbackMetadata(Base):
    __tablename__ = "feedback_metadata"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

# ─── In-memory "MongoDB" substitute ──────────────────────────────────────────

feedback_content_store: dict[str, dict] = {}

# ─── Security ─────────────────────────────────────────────────────────────────

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": subject, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

# ─── Schemas ──────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    org_name: str = "My Organization"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    model_config = {"from_attributes": True}

class FeedbackCreate(BaseModel):
    text: str
    org_id: str

class FeedbackMetadataResponse(BaseModel):
    id: str
    org_id: str
    status: str
    sentiment_score: float | None = None
    category: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}

class FeedbackDetailResponse(FeedbackMetadataResponse):
    raw_text: str | None = None
    cleaned_text: str | None = None
    keywords: list[str] = []

class FeedbackListResponse(BaseModel):
    items: list[FeedbackMetadataResponse]
    total: int
    page: int
    page_size: int

class SentimentTrendPoint(BaseModel):
    date: str
    avg_sentiment: float
    count: int

class CategoryCount(BaseModel):
    category: str
    count: int

class VolumePoint(BaseModel):
    date: str
    count: int

# ─── Dependencies ─────────────────────────────────────────────────────────────

async def get_db():
    async with async_session() as session:
        yield session

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> str:
    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return subject

# ─── Simple AI simulation (no heavy ML dependencies needed) ──────────────────

def simple_sentiment(text: str) -> float:
    """Simulate sentiment analysis with keyword matching."""
    positive = ["great", "love", "amazing", "excellent", "awesome", "good", "fantastic",
                "wonderful", "best", "happy", "thank", "perfect", "beautiful", "helpful"]
    negative = ["bad", "terrible", "worst", "hate", "awful", "poor", "horrible",
                "broken", "bug", "crash", "error", "fail", "disappoint", "slow"]
    text_lower = text.lower()
    pos = sum(1 for w in positive if w in text_lower)
    neg = sum(1 for w in negative if w in text_lower)
    if pos + neg == 0:
        return round(random.uniform(-0.2, 0.2), 4)
    return round((pos - neg) / (pos + neg), 4)

def simple_keywords(text: str) -> list[str]:
    """Extract simple keywords."""
    stop = {"the","a","an","is","are","was","were","be","been","have","has","had",
            "do","does","did","will","would","could","should","to","of","in","for",
            "on","with","at","by","from","as","and","but","or","not","so","it","i",
            "me","my","we","you","your","he","she","they","this","that","very","just"}
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    filtered = [w for w in words if w not in stop]
    freq = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]

def simple_categorize(text: str, sentiment: float) -> str:
    """Categorize feedback."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["bug", "error", "crash", "broken", "fix"]):
        return "bug"
    if any(w in text_lower for w in ["feature", "request", "add", "want", "wish"]):
        return "feature_request"
    if sentiment > 0.3:
        return "praise"
    if sentiment < -0.3:
        return "complaint"
    if any(w in text_lower for w in ["how", "what", "why", "help", "question"]):
        return "question"
    return "general"

# ─── App ──────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="InsightFlow", version="1.0.0 (local)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Auth endpoints ──────────────────────────────────────────────────────────

@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    await db.flush()
    org = Organization(name=data.org_name, owner_id=user.id)
    db.add(org)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id))

# ─── Feedback endpoints ──────────────────────────────────────────────────────

@app.post("/api/feedback", response_model=FeedbackMetadataResponse, status_code=201)
async def create_feedback(
    data: FeedbackCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Process immediately (no Celery in local mode)
    cleaned = re.sub(r"<[^>]+>", "", data.text.strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    sentiment = simple_sentiment(cleaned)
    keywords = simple_keywords(cleaned)
    category = simple_categorize(cleaned, sentiment)

    feedback = FeedbackMetadata(
        org_id=data.org_id,
        status="processed",
        sentiment_score=sentiment,
        category=category,
        raw_text=data.text,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    # Store in memory "mongo"
    feedback_content_store[feedback.id] = {
        "raw_text": data.text,
        "cleaned_text": cleaned,
        "keywords": keywords,
    }

    return FeedbackMetadataResponse.model_validate(feedback)

@app.get("/api/feedback", response_model=FeedbackListResponse)
async def list_feedback(
    org_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    category: str | None = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = select(FeedbackMetadata).where(FeedbackMetadata.org_id == org_id)
    count_q = select(func.count(FeedbackMetadata.id)).where(FeedbackMetadata.org_id == org_id)
    if status:
        query = query.where(FeedbackMetadata.status == status)
        count_q = count_q.where(FeedbackMetadata.status == status)
    if category:
        query = query.where(FeedbackMetadata.category == category)
        count_q = count_q.where(FeedbackMetadata.category == category)
    query = query.order_by(FeedbackMetadata.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    items = list((await db.execute(query)).scalars().all())
    total = (await db.execute(count_q)).scalar_one()
    return FeedbackListResponse(
        items=[FeedbackMetadataResponse.model_validate(i) for i in items],
        total=total, page=page, page_size=page_size,
    )

@app.get("/api/feedback/{feedback_id}", response_model=FeedbackDetailResponse)
async def get_feedback(
    feedback_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    fb = (await db.execute(select(FeedbackMetadata).where(FeedbackMetadata.id == feedback_id))).scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    content = feedback_content_store.get(fb.id, {})
    return FeedbackDetailResponse(
        id=fb.id, org_id=fb.org_id, status=fb.status,
        sentiment_score=fb.sentiment_score, category=fb.category,
        created_at=fb.created_at, raw_text=content.get("raw_text", fb.raw_text),
        cleaned_text=content.get("cleaned_text"), keywords=content.get("keywords", []),
    )

# ─── Analytics endpoints ─────────────────────────────────────────────────────

@app.get("/api/analytics/sentiment-trends")
async def sentiment_trends(
    org_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(
            func.date(FeedbackMetadata.created_at).label("date"),
            func.avg(FeedbackMetadata.sentiment_score).label("avg_sentiment"),
            func.count(FeedbackMetadata.id).label("count"),
        )
        .where(FeedbackMetadata.org_id == org_id, FeedbackMetadata.sentiment_score.isnot(None))
        .group_by(func.date(FeedbackMetadata.created_at))
        .order_by(func.date(FeedbackMetadata.created_at))
        .limit(days)
    )
    result = await db.execute(query)
    trends = [{"date": str(r.date), "avg_sentiment": round(float(r.avg_sentiment), 3), "count": r.count} for r in result.all()]
    return {"trends": trends}

@app.get("/api/analytics/category-breakdown")
async def category_breakdown(
    org_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(
            func.coalesce(FeedbackMetadata.category, "uncategorized").label("category"),
            func.count(FeedbackMetadata.id).label("count"),
        )
        .where(FeedbackMetadata.org_id == org_id)
        .group_by(FeedbackMetadata.category)
    )
    result = await db.execute(query)
    return {"categories": [{"category": r.category, "count": r.count} for r in result.all()]}

@app.get("/api/analytics/volume-over-time")
async def volume_over_time(
    org_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(
            func.date(FeedbackMetadata.created_at).label("date"),
            func.count(FeedbackMetadata.id).label("count"),
        )
        .where(FeedbackMetadata.org_id == org_id)
        .group_by(func.date(FeedbackMetadata.created_at))
        .order_by(func.date(FeedbackMetadata.created_at))
        .limit(days)
    )
    result = await db.execute(query)
    return {"volumes": [{"date": str(r.date), "count": r.count} for r in result.all()]}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "app": "InsightFlow", "mode": "local"}

# ─── Org lookup helper ────────────────────────────────────────────────────────

@app.get("/api/organizations")
async def list_organizations(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Organization).where(Organization.owner_id == user_id))
    orgs = result.scalars().all()
    return [{"id": o.id, "name": o.name} for o in orgs]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run_local:app", host="0.0.0.0", port=8000, reload=True)
