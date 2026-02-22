"""Analytics service layer with Redis caching."""

import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_redis
from app.repositories import feedback_repo
from app.schemas.analytics import (
    SentimentTrendsResponse,
    CategoryBreakdownResponse,
    VolumeOverTimeResponse,
)


async def _get_cached(key: str) -> dict | None:
    """Get cached data from Redis."""
    redis = get_redis()
    if redis:
        data = await redis.get(key)
        if data:
            return json.loads(data)
    return None


async def _set_cached(key: str, data: dict) -> None:
    """Set data in Redis cache with TTL."""
    redis = get_redis()
    if redis:
        await redis.setex(key, settings.CACHE_TTL, json.dumps(data))


async def invalidate_analytics_cache(org_id: uuid.UUID) -> None:
    """Invalidate all analytics cache for an organization."""
    redis = get_redis()
    if redis:
        keys = [
            f"analytics:sentiment:{org_id}",
            f"analytics:categories:{org_id}",
            f"analytics:volume:{org_id}",
        ]
        for key in keys:
            await redis.delete(key)


async def get_sentiment_trends(
    db: AsyncSession, org_id: uuid.UUID, days: int = 30
) -> SentimentTrendsResponse:
    """Get sentiment trends with caching."""
    cache_key = f"analytics:sentiment:{org_id}"
    cached = await _get_cached(cache_key)
    if cached:
        return SentimentTrendsResponse(**cached)

    trends = await feedback_repo.get_sentiment_trends(db, org_id, days)
    response = SentimentTrendsResponse(trends=trends)
    await _set_cached(cache_key, response.model_dump())
    return response


async def get_category_breakdown(
    db: AsyncSession, org_id: uuid.UUID
) -> CategoryBreakdownResponse:
    """Get category breakdown with caching."""
    cache_key = f"analytics:categories:{org_id}"
    cached = await _get_cached(cache_key)
    if cached:
        return CategoryBreakdownResponse(**cached)

    categories = await feedback_repo.get_category_breakdown(db, org_id)
    response = CategoryBreakdownResponse(categories=categories)
    await _set_cached(cache_key, response.model_dump())
    return response


async def get_volume_over_time(
    db: AsyncSession, org_id: uuid.UUID, days: int = 30
) -> VolumeOverTimeResponse:
    """Get volume over time with caching."""
    cache_key = f"analytics:volume:{org_id}"
    cached = await _get_cached(cache_key)
    if cached:
        return VolumeOverTimeResponse(**cached)

    volumes = await feedback_repo.get_volume_over_time(db, org_id, days)
    response = VolumeOverTimeResponse(volumes=volumes)
    await _set_cached(cache_key, response.model_dump())
    return response
