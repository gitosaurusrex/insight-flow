"""Feedback API endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackMetadataResponse,
    FeedbackDetailResponse,
    FeedbackListResponse,
)
from app.services import feedback_service

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackMetadataResponse, status_code=201)
async def create_feedback(
    data: FeedbackCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Submit new feedback for AI processing."""
    return await feedback_service.submit_feedback(db, data, user_id)


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    org_id: uuid.UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    category: str | None = Query(None),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List feedback with pagination and filters."""
    return await feedback_service.list_feedback(
        db, org_id, page, page_size, status, category
    )


@router.get("/{feedback_id}", response_model=FeedbackDetailResponse)
async def get_feedback(
    feedback_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed feedback including processed content."""
    return await feedback_service.get_feedback(db, feedback_id)
