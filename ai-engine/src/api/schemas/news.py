"""
Pydantic models for API schemas
"""

from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal


class NewsItem(BaseModel):
    """Single news item"""
    id: Optional[str] = None
    title: str
    translated_title: Optional[str] = None
    url: str
    source: str
    category: Optional[str] = None
    score: Optional[int] = None
    llm_score: Optional[Decimal] = None
    final_score: Optional[Decimal] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    raw_summary: Optional[str] = None
    published_date: Optional[date] = None
    timestamp: Optional[str] = None


class NewsListResponse(BaseModel):
    """Response for news list"""
    news: List[NewsItem]
    total: int
    date: str


class IngestRequest(BaseModel):
    """Request for triggering ingest"""
    sources: Optional[List[str]] = None
    clear_collection: bool = False


class IngestResponse(BaseModel):
    """Response for ingest operation"""
    success: bool
    message: str
    stats: dict


class ScoreRequest(BaseModel):
    """Request for scoring news"""
    news_ids: Optional[List[str]] = None  # If None, score all unprocessed news


class ScoreResponse(BaseModel):
    """Response for scoring operation"""
    success: bool
    message: str
    processed: int


class SummarizeRequest(BaseModel):
    """Request for summarizing news"""
    news_ids: Optional[List[str]] = None
    summary_type: str = "deep"  # "deep" or "simple"


class SummarizeResponse(BaseModel):
    """Response for summarize operation"""
    success: bool
    message: str
    processed: int


class HealthResponse(BaseModel):
    """Response for health check"""
    status: str
    qdrant_connected: bool
    llm_configured: bool
    timestamp: str
