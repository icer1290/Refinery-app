"""SQLAlchemy ORM models for database tables."""

import uuid
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    ForeignKey,
    JSON,
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class NewsArticle(Base):
    """News article model."""

    __tablename__ = "news_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    original_title: Mapped[str] = mapped_column(Text, nullable=False)
    original_description: Mapped[str | None] = mapped_column(Text)
    chinese_title: Mapped[str | None] = mapped_column(Text)
    chinese_summary: Mapped[str | None] = mapped_column(Text)
    full_content: Mapped[str | None] = mapped_column(Text)

    # Scores
    total_score: Mapped[float | None] = mapped_column(Float)
    industry_impact_score: Mapped[float | None] = mapped_column(Float)
    milestone_score: Mapped[float | None] = mapped_column(Float)
    attention_score: Mapped[float | None] = mapped_column(Float)

    # Timestamps
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Reflection
    reflection_retries: Mapped[int] = mapped_column(Integer, default=0)
    reflection_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    reflection_feedback: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON)

    # Relationship to embedding
    embedding: Mapped[Optional["ArticleEmbedding"]] = relationship(
        "ArticleEmbedding", back_populates="article", uselist=False
    )

    __table_args__ = (
        Index("ix_news_articles_source_url", source_url),
        Index("ix_news_articles_published_at", published_at),
        Index("ix_news_articles_total_score", total_score),
    )


class ArticleEmbedding(Base):
    """Article embedding model with pgvector."""

    __tablename__ = "article_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    article: Mapped["NewsArticle"] = relationship(
        "NewsArticle", back_populates="embedding"
    )

    __table_args__ = (
        Index("ix_article_embeddings_article_id", article_id, unique=True),
        Index("ix_article_embeddings_content_hash", content_hash),
    )


class RSSFeedSource(Base):
    """RSS feed source configuration."""

    __tablename__ = "rss_feed_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetch_error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_rss_feed_sources_url", url),
        Index("ix_rss_feed_sources_is_active", is_active),
    )


class WorkflowRun(Base):
    """Workflow execution record."""

    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="running")

    # Statistics
    total_feeds_fetched: Mapped[int] = mapped_column(Integer, default=0)
    total_articles_found: Mapped[int] = mapped_column(Integer, default=0)
    total_articles_after_dedup: Mapped[int] = mapped_column(Integer, default=0)
    total_articles_after_scoring: Mapped[int] = mapped_column(Integer, default=0)
    total_articles_stored: Mapped[int] = mapped_column(Integer, default=0)

    # Error tracking
    errors: Mapped[list | None] = mapped_column(JSON)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON)

    __table_args__ = (Index("ix_workflow_runs_started_at", started_at),)