"""Embedding service using OpenAI-compatible APIs."""

import traceback
from typing import List, Optional

from langchain_openai import OpenAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core import get_logger
from app.core.exceptions import EmbeddingError

logger = get_logger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating text embeddings using OpenAI-compatible APIs."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model or settings.openai_embedding_model
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url

        if not self.api_key:
            raise EmbeddingError("API key not configured")

        # Build OpenAIEmbeddings with optional custom base_url
        embeddings_kwargs = {
            "model": self.model,
            "openai_api_key": self.api_key,
        }

        # Add base_url if provided (for DashScope, etc.)
        if self.base_url:
            embeddings_kwargs["openai_api_base"] = self.base_url

        self.embeddings = OpenAIEmbeddings(**embeddings_kwargs)

        logger.info(
            "Embedding service initialized",
            model=self.model,
            base_url=self.base_url or "default",
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            # Truncate text if too long (OpenAI has token limits)
            truncated_text = self._truncate_text(text)

            embedding = await self.embeddings.aembed_query(truncated_text)

            logger.debug(
                "Generated embedding",
                text_length=len(text),
                embedding_dim=len(embedding),
            )

            return embedding

        except Exception as e:
            # 详细错误日志
            error_detail = f"{type(e).__name__}: {str(e)}"
            logger.error(
                "Embedding generation failed",
                error=error_detail,
                model=self.model,
                text_preview=text[:100],
                traceback=traceback.format_exc(),
            )
            raise EmbeddingError(
                f"Failed to generate embedding: {error_detail}",
                {"error": str(e), "model": self.model},
            )

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            # Truncate texts
            truncated_texts = [self._truncate_text(text) for text in texts]

            embeddings = await self.embeddings.aembed_documents(truncated_texts)

            logger.info(
                "Generated batch embeddings",
                count=len(embeddings),
                model=self.model,
            )

            return embeddings

        except Exception as e:
            error_detail = f"{type(e).__name__}: {str(e)}"
            logger.error(
                "Batch embedding generation failed",
                error=error_detail,
                model=self.model,
                count=len(texts),
                traceback=traceback.format_exc(),
            )
            raise EmbeddingError(
                f"Failed to generate batch embeddings: {error_detail}",
                {"error": str(e), "model": self.model, "count": len(texts)},
            )

    def _truncate_text(self, text: str, max_tokens: int = 8000) -> str:
        """Truncate text to fit within token limits.

        OpenAI embedding models have token limits. We use a conservative
        character-based approximation.

        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens

        Returns:
            Truncated text
        """
        # Rough approximation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        if len(text) > max_chars:
            return text[:max_chars] + "..."
        return text

    async def compute_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between -1 and 1
        """
        # Compute dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))

        # Compute magnitudes
        mag1 = sum(a * a for a in embedding1) ** 0.5
        mag2 = sum(b * b for b in embedding2) ** 0.5

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service