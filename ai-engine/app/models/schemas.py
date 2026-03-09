"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# === Article Schemas ===


class ArticleBase(BaseModel):
    """Base article schema."""

    source_name: str
    source_url: str
    original_title: str
    original_description: Optional[str] = None
    published_at: Optional[datetime] = None


class ArticleCreate(ArticleBase):
    """Schema for creating an article."""

    pass


class ArticleResponse(ArticleBase):
    """Schema for article response."""

    id: UUID
    chinese_title: Optional[str] = None
    chinese_summary: Optional[str] = None
    full_content: Optional[str] = None
    total_score: Optional[float] = None
    industry_impact_score: Optional[float] = None
    milestone_score: Optional[float] = None
    attention_score: Optional[float] = None
    processed_at: datetime
    reflection_retries: int = 0
    reflection_passed: bool = False
    is_published: bool = False
    metadata_: Optional[dict[str, Any]] = None

    # DeepSearch Report
    deepsearch_report: Optional[str] = None
    deepsearch_performed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    """Schema for article list response."""

    articles: list[ArticleResponse]
    total: int
    page: int
    page_size: int


# === RSS Feed Schemas ===


class RSSFeedBase(BaseModel):
    """Base RSS feed schema."""

    name: str
    url: str
    is_active: bool = True


class RSSFeedCreate(RSSFeedBase):
    """Schema for creating an RSS feed."""

    pass


class RSSFeedResponse(RSSFeedBase):
    """Schema for RSS feed response."""

    id: UUID
    last_fetched_at: Optional[datetime] = None
    fetch_error_count: int = 0
    last_error: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RSSFeedListResponse(BaseModel):
    """Schema for RSS feed list response."""

    feeds: list[RSSFeedResponse]
    total: int


# === Workflow Schemas ===


class WorkflowRunResponse(BaseModel):
    """Schema for workflow run response."""

    id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    total_feeds_fetched: int = 0
    total_articles_found: int = 0
    total_articles_after_dedup: int = 0
    total_articles_after_scoring: int = 0
    total_articles_stored: int = 0
    errors: Optional[list[dict[str, Any]]] = None
    metadata_: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class WorkflowRunListResponse(BaseModel):
    """Schema for workflow run list response."""

    runs: list[WorkflowRunResponse]
    total: int


class WorkflowTriggerRequest(BaseModel):
    """Schema for triggering a workflow run."""

    feed_urls: Optional[list[str]] = Field(
        default=None, description="Specific RSS feeds to fetch, or None for all"
    )
    score_threshold: Optional[float] = Field(
        default=None, description="Override default score threshold"
    )
    force: bool = Field(
        default=False, description="Force reprocessing of existing articles"
    )


# === Scoring Schemas ===


class ScoringResult(BaseModel):
    """Schema for article scoring result."""

    industry_impact_score: float = Field(ge=0, le=10)
    milestone_score: float = Field(ge=0, le=10)
    attention_score: float = Field(ge=0, le=10)
    total_score: float = Field(ge=0, le=10)
    reasoning: Optional[str] = None


# === Translation Schemas ===


class TranslationResult(BaseModel):
    """Schema for translation result."""

    chinese_title: str
    chinese_summary: str
    entities_preserved: list[str] = []


# === Reflection Schemas ===


class ReflectionResult(BaseModel):
    """Schema for reflection result."""

    passed: bool
    feedback: Optional[str] = None
    issues: list[str] = []


# === Error Schemas ===


class ErrorResponse(BaseModel):
    """Schema for error response."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# === Deep Search Schemas ===


class DeepSearchRequest(BaseModel):
    """Schema for deep search request."""

    article_id: str = Field(..., description="UUID of the article to analyze")
    max_iterations: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of ReAct iterations",
    )


class ToolCallInfo(BaseModel):
    """Schema for tool call information."""

    tool_name: str
    tool_input: dict[str, Any]
    tool_output: str
    iteration: int


class CollectedInfoResponse(BaseModel):
    """Schema for collected information."""

    source: str
    content: str
    relevance: str
    metadata: dict[str, Any]


class DeepSearchResponse(BaseModel):
    """Schema for deep search response."""

    article_id: str
    article_title: str
    final_report: str
    tools_used: list[ToolCallInfo]
    collected_info: list[CollectedInfoResponse]
    iterations: int
    is_complete: bool
    errors: list[dict[str, Any]] = []