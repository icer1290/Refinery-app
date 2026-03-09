"""Writer Agent - Content extraction and translation."""

import asyncio
from typing import Any

from app.agents.base import BaseAgent
from app.config import get_settings
from app.services.llm_service import LLMService, get_llm_service
from app.services.web_extractor import web_extractor

settings = get_settings()


class WriterAgent(BaseAgent):
    """Agent responsible for extracting content and generating translations."""

    def __init__(self, max_concurrent: int | None = None):
        super().__init__("Writer")
        self.llm_service: LLMService | None = None
        self.max_concurrent = max_concurrent or settings.max_concurrent_writers
        self._semaphore: asyncio.Semaphore | None = None

    def _get_llm_service(self) -> LLMService:
        """Lazily initialize LLM service."""
        if self.llm_service is None:
            self.llm_service = get_llm_service()
        return self.llm_service

    async def execute(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process articles: extract content and translate.

        Args:
            articles: List of scored articles to process

        Returns:
            List of articles with extracted content and translations
        """
        if not articles:
            return []

        # Initialize semaphore for concurrency control
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

        # Process articles concurrently
        tasks = [self._process_article(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect successful results
        processed_articles = []
        for article, result in zip(articles, results):
            if isinstance(result, Exception):
                self.logger.warning(
                    "Failed to process article",
                    article_url=article.get("source_url"),
                    error=str(result),
                )
                continue
            processed_articles.append(result)

        self.logger.info(
            "Writer phase complete",
            articles_input=len(articles),
            articles_processed=len(processed_articles),
        )

        return processed_articles

    async def _process_article(self, article: dict[str, Any]) -> dict[str, Any]:
        """Process a single article: extract content and translate.

        Args:
            article: Article to process

        Returns:
            Article with content and translation fields

        Raises:
            ValueError: If full_content is empty (article should be discarded)
        """
        async with self._semaphore:
            # Extract full content from web page
            full_content = await self._extract_content(article["source_url"])

            # Discard article if no content was extracted
            if not full_content:
                raise ValueError(
                    "No content extracted, discarding article",
                    {"url": article["source_url"]},
                )

            # Generate Chinese title and summary
            llm = self._get_llm_service()
            translation = await llm.translate_and_summarize(
                title=article["original_title"],
                content=full_content or article.get("original_description", ""),
                entities_to_preserve=article.get("entities_preserved"),
            )

            # Update article with processed content
            processed_article = article.copy()
            processed_article.update({
                "full_content": full_content,
                "chinese_title": translation.chinese_title,
                "chinese_summary": translation.chinese_summary,
                "entities_preserved": translation.entities_preserved,
            })

            return processed_article

    async def _extract_content(self, url: str) -> str | None:
        """Extract content from URL with error handling.

        Args:
            url: URL to extract from

        Returns:
            Extracted content or None
        """
        try:
            content = await web_extractor.extract_content(url)
            return content if content else None
        except Exception as e:
            self.logger.warning(
                "Failed to extract content",
                url=url,
                error=str(e),
            )
            return None


# Singleton instance
writer_agent = WriterAgent()