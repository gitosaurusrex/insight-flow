"""Tests for feedback endpoints."""

import uuid
from unittest.mock import patch, AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_feedback_unauthorized(client: AsyncClient):
    """Test feedback creation without auth fails."""
    response = await client.post(
        "/api/feedback",
        json={"text": "Great product!", "org_id": str(uuid.uuid4())},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_feedback_unauthorized(client: AsyncClient):
    """Test listing feedback without auth fails."""
    response = await client.get(
        "/api/feedback", params={"org_id": str(uuid.uuid4())}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_feedback_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting non-existent feedback returns 404."""
    response = await client.get(
        f"/api/feedback/{uuid.uuid4()}", headers=auth_headers
    )
    assert response.status_code == 404
