"""Feedback service layer."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import feedback_repo
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackMetadataResponse,
    FeedbackDetailResponse,
    FeedbackListResponse,
)
from app.tasks.feedback_tasks import process_feedback


async def submit_feedback(
    db: AsyncSession, data: FeedbackCreate, user_id: uuid.UUID
) -> FeedbackMetadataResponse:
    """Submit new feedback: store in PG + Mongo, enqueue AI task."""
    metadata = await feedback_repo.create_feedback_metadata(db, data.org_id)
    await db.commit()

    await feedback_repo.store_feedback_content(metadata.id, data.text)

    # Enqueue background processing
    process_feedback.delay(str(metadata.id))

    return FeedbackMetadataResponse.model_validate(metadata)


async def get_feedback(
    db: AsyncSession, feedback_id: uuid.UUID
) -> FeedbackDetailResponse:
    """Get full feedback detail (PG metadata + Mongo content)."""
    metadata = await feedback_repo.get_feedback_by_id(db, feedback_id)
    if not metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    content = await feedback_repo.get_feedback_content(feedback_id)

    return FeedbackDetailResponse(
        id=metadata.id,
        org_id=metadata.org_id,
        status=metadata.status,
        sentiment_score=metadata.sentiment_score,
        category=metadata.category,
        created_at=metadata.created_at,
        raw_text=content.get("raw_text") if content else None,
        cleaned_text=content.get("cleaned_text") if content else None,
        keywords=content.get("keywords", []) if content else [],
    )


async def list_feedback(
    db: AsyncSession,
    org_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    category: str | None = None,
) -> FeedbackListResponse:
    """List feedback with pagination and filtering."""
    items, total = await feedback_repo.list_feedback(
        db, org_id, page, page_size, status_filter, category
    )
    return FeedbackListResponse(
        items=[FeedbackMetadataResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )
