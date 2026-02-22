"""Feedback Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    text: str
    org_id: uuid.UUID


class FeedbackMetadataResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
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
