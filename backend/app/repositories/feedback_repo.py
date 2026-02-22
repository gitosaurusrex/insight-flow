"""Feedback repository for PostgreSQL and MongoDB operations."""

import uuid
from datetime import datetime

from sqlalchemy import select, func, case, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import FeedbackMetadata
from app.core.database import get_mongo


async def create_feedback_metadata(
    db: AsyncSession, org_id: uuid.UUID
) -> FeedbackMetadata:
    """Create feedback metadata in PostgreSQL."""
    feedback = FeedbackMetadata(org_id=org_id)
    db.add(feedback)
    await db.flush()
    return feedback


async def get_feedback_by_id(
    db: AsyncSession, feedback_id: uuid.UUID
) -> FeedbackMetadata | None:
    """Fetch feedback metadata by ID."""
    result = await db.execute(
        select(FeedbackMetadata).where(FeedbackMetadata.id == feedback_id)
    )
    return result.scalar_one_or_none()


async def list_feedback(
    db: AsyncSession,
    org_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    category: str | None = None,
) -> tuple[list[FeedbackMetadata], int]:
    """List feedback with pagination and filters. Returns (items, total)."""
    query = select(FeedbackMetadata).where(FeedbackMetadata.org_id == org_id)
    count_query = select(func.count(FeedbackMetadata.id)).where(
        FeedbackMetadata.org_id == org_id
    )

    if status:
        query = query.where(FeedbackMetadata.status == status)
        count_query = count_query.where(FeedbackMetadata.status == status)
    if category:
        query = query.where(FeedbackMetadata.category == category)
        count_query = count_query.where(FeedbackMetadata.category == category)

    query = query.order_by(FeedbackMetadata.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    total_result = await db.execute(count_query)

    return list(result.scalars().all()), total_result.scalar_one()


async def update_feedback_metadata(
    db: AsyncSession,
    feedback_id: uuid.UUID,
    status: str | None = None,
    sentiment_score: float | None = None,
    category: str | None = None,
) -> None:
    """Update feedback metadata fields."""
    feedback = await get_feedback_by_id(db, feedback_id)
    if feedback:
        if status is not None:
            feedback.status = status
        if sentiment_score is not None:
            feedback.sentiment_score = sentiment_score
        if category is not None:
            feedback.category = category
        await db.flush()


# --- MongoDB operations ---

async def store_feedback_content(
    metadata_id: uuid.UUID, raw_text: str
) -> None:
    """Store raw feedback content in MongoDB."""
    mongo = get_mongo()
    await mongo.feedback_content.insert_one({
        "metadata_id": str(metadata_id),
        "raw_text": raw_text,
        "cleaned_text": None,
        "embedding": None,
        "keywords": [],
        "processed_at": None,
    })


async def get_feedback_content(metadata_id: uuid.UUID) -> dict | None:
    """Retrieve feedback content from MongoDB."""
    mongo = get_mongo()
    return await mongo.feedback_content.find_one(
        {"metadata_id": str(metadata_id)}, {"_id": 0}
    )


async def update_feedback_content(
    metadata_id: uuid.UUID,
    cleaned_text: str | None = None,
    embedding: list[float] | None = None,
    keywords: list[str] | None = None,
) -> None:
    """Update processed feedback content in MongoDB."""
    mongo = get_mongo()
    update_fields: dict = {"processed_at": datetime.utcnow()}
    if cleaned_text is not None:
        update_fields["cleaned_text"] = cleaned_text
    if embedding is not None:
        update_fields["embedding"] = embedding
    if keywords is not None:
        update_fields["keywords"] = keywords

    await mongo.feedback_content.update_one(
        {"metadata_id": str(metadata_id)}, {"$set": update_fields}
    )


# --- Analytics queries ---

async def get_sentiment_trends(
    db: AsyncSession, org_id: uuid.UUID, days: int = 30
) -> list[dict]:
    """Get daily average sentiment scores."""
    query = (
        select(
            cast(FeedbackMetadata.created_at, Date).label("date"),
            func.avg(FeedbackMetadata.sentiment_score).label("avg_sentiment"),
            func.count(FeedbackMetadata.id).label("count"),
        )
        .where(
            FeedbackMetadata.org_id == org_id,
            FeedbackMetadata.sentiment_score.isnot(None),
        )
        .group_by(cast(FeedbackMetadata.created_at, Date))
        .order_by(cast(FeedbackMetadata.created_at, Date))
        .limit(days)
    )
    result = await db.execute(query)
    return [
        {"date": str(row.date), "avg_sentiment": round(float(row.avg_sentiment), 3), "count": row.count}
        for row in result.all()
    ]


async def get_category_breakdown(
    db: AsyncSession, org_id: uuid.UUID
) -> list[dict]:
    """Get feedback counts by category."""
    query = (
        select(
            func.coalesce(FeedbackMetadata.category, "uncategorized").label("category"),
            func.count(FeedbackMetadata.id).label("count"),
        )
        .where(FeedbackMetadata.org_id == org_id)
        .group_by(FeedbackMetadata.category)
        .order_by(func.count(FeedbackMetadata.id).desc())
    )
    result = await db.execute(query)
    return [{"category": row.category, "count": row.count} for row in result.all()]


async def get_volume_over_time(
    db: AsyncSession, org_id: uuid.UUID, days: int = 30
) -> list[dict]:
    """Get daily feedback volume."""
    query = (
        select(
            cast(FeedbackMetadata.created_at, Date).label("date"),
            func.count(FeedbackMetadata.id).label("count"),
        )
        .where(FeedbackMetadata.org_id == org_id)
        .group_by(cast(FeedbackMetadata.created_at, Date))
        .order_by(cast(FeedbackMetadata.created_at, Date))
        .limit(days)
    )
    result = await db.execute(query)
    return [{"date": str(row.date), "count": row.count} for row in result.all()]
