"""Tests for embedding service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.embedding import EmbeddingService


@pytest.fixture
def mock_settings():
    with patch("app.services.embedding.settings") as mock:
        mock.openai_embedding_model = "text-embedding-3-small"
        mock.openai_api_key = "test-key"
        yield mock


@pytest.mark.asyncio
async def test_truncate_text(mock_settings):
    """Test text truncation."""
    service = EmbeddingService(api_key="test-key")

    short_text = "Short text"
    long_text = "x" * 40000

    truncated = service._truncate_text(long_text, max_tokens=8000)
    assert len(truncated) < len(long_text)
    assert truncated.endswith("...")

    not_truncated = service._truncate_text(short_text)
    assert not_truncated == short_text


@pytest.mark.asyncio
async def test_compute_similarity(mock_settings):
    """Test cosine similarity computation."""
    service = EmbeddingService(api_key="test-key")

    embedding1 = [1.0, 0.0, 0.0]
    embedding2 = [1.0, 0.0, 0.0]
    embedding3 = [0.0, 1.0, 0.0]

    # Same vector
    similarity = await service.compute_similarity(embedding1, embedding2)
    assert similarity == pytest.approx(1.0, rel=0.01)

    # Orthogonal vector
    similarity = await service.compute_similarity(embedding1, embedding3)
    assert similarity == pytest.approx(0.0, abs=0.01)