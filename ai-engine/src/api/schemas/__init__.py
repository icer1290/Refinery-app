"""
API schemas
"""

from src.api.schemas.news import (
    NewsItem, NewsListResponse,
    IngestRequest, IngestResponse,
    ScoreRequest, ScoreResponse,
    SummarizeRequest, SummarizeResponse,
    HealthResponse
)

__all__ = [
    "NewsItem", "NewsListResponse",
    "IngestRequest", "IngestResponse",
    "ScoreRequest", "ScoreResponse",
    "SummarizeRequest", "SummarizeResponse",
    "HealthResponse"
]
