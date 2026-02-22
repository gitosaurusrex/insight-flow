"""Analytics Pydantic schemas."""

from pydantic import BaseModel


class SentimentTrendPoint(BaseModel):
    date: str
    avg_sentiment: float
    count: int


class SentimentTrendsResponse(BaseModel):
    trends: list[SentimentTrendPoint]


class CategoryCount(BaseModel):
    category: str
    count: int


class CategoryBreakdownResponse(BaseModel):
    categories: list[CategoryCount]


class VolumePoint(BaseModel):
    date: str
    count: int


class VolumeOverTimeResponse(BaseModel):
    volumes: list[VolumePoint]
