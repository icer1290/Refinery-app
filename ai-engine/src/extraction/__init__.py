"""
Extraction module
"""

from src.extraction.content_extractor import (
    extract_content_from_url,
    extract_content_with_metadata,
    extract_batch,
    extract_article_content,
    batch_extract_articles
)

__all__ = [
    "extract_content_from_url",
    "extract_content_with_metadata",
    "extract_batch",
    "extract_article_content",
    "batch_extract_articles"
]
