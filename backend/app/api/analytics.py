"""Analytics API endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.analytics import (
    SentimentTrendsResponse,
    CategoryBreakdownResponse,
    VolumeOverTimeResponse,
)
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/sentiment-trends", response_model=SentimentTrendsResponse)
async def sentiment_trends(
    org_id: uuid.UUID = Query(...),
    days: int = Query(30, ge=1, le=365),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get sentiment score trends over time."""
    return await analytics_service.get_sentiment_trends(db, org_id, days)


@router.get("/category-breakdown", response_model=CategoryBreakdownResponse)
async def category_breakdown(
    org_id: uuid.UUID = Query(...),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get feedback count breakdown by category."""
    return await analytics_service.get_category_breakdown(db, org_id)


@router.get("/volume-over-time", response_model=VolumeOverTimeResponse)
async def volume_over_time(
    org_id: uuid.UUID = Query(...),
    days: int = Query(30, ge=1, le=365),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get feedback submission volume over time."""
    return await analytics_service.get_volume_over_time(db, org_id, days)
