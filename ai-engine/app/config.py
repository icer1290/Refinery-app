"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/news_aggregator"

    # LLM API Configuration
    openai_api_key: str = ""
    openai_base_url: Optional[str] = None  # For custom API endpoints (DashScope, etc.)
    openai_embedding_model: str = "text-embedding-v4"
    openai_chat_model: str = "qwen3.5-35b-a3b"

    # Deduplication
    dedup_similarity_threshold: float = 0.85

    # Scoring
    score_threshold: float = 5.0

    # Reflection
    max_reflection_retries: int = 3

    # Concurrency
    max_concurrent_scorers: int = 5
    max_concurrent_writers: int = 3

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # RSS Feed Sources
    default_rss_feeds: List[str] = [
        # Tech News
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "https://www.techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.feedburner.com/oreilly/radar",
        "https://www.wired.com/feed/rss",
        "https://feeds.feedburner.com/TechCrunch/",
        "https://www.engadget.com/rss.xml",
        "https://gizmodo.com/rss",
        "https://venturebeat.com/feed/",
        # AI/ML News
        "https://www.artificialintelligence-news.com/feed/",
        "https://openai.com/blog/rss.xml",
        "https://deepmind.google/discover/blog/rss/",
        "https://huggingface.co/blog/feed.xml",
        # Developer News
        "https://github.blog/feed/",
        "https://stackoverflow.blog/feed/",
        "https://news.ycombinator.com/rss",
    ]

    # Deep Search Configuration
    deep_search_max_iterations: int = 5
    web_search_provider: str = "duckduckgo"  # or "tavily"
    web_search_api_key: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()