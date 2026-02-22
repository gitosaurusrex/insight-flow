"""Tests for analytics endpoints."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sentiment_trends_unauthorized(client: AsyncClient):
    """Test analytics without auth fails."""
    response = await client.get(
        "/api/analytics/sentiment-trends", params={"org_id": str(uuid.uuid4())}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_sentiment_trends(client: AsyncClient, auth_headers: dict):
    """Test sentiment trends endpoint returns data."""
    response = await client.get(
        "/api/analytics/sentiment-trends",
        params={"org_id": str(uuid.uuid4())},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "trends" in response.json()


@pytest.mark.asyncio
async def test_category_breakdown(client: AsyncClient, auth_headers: dict):
    """Test category breakdown endpoint returns data."""
    response = await client.get(
        "/api/analytics/category-breakdown",
        params={"org_id": str(uuid.uuid4())},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "categories" in response.json()


@pytest.mark.asyncio
async def test_volume_over_time(client: AsyncClient, auth_headers: dict):
    """Test volume over time endpoint returns data."""
    response = await client.get(
        "/api/analytics/volume-over-time",
        params={"org_id": str(uuid.uuid4())},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "volumes" in response.json()
