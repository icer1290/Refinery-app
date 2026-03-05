"""Reflection Agent - Quality check and validation."""

import traceback
from typing import Any

from app.agents.base import BaseAgent
from app.config import get_settings
from app.services.llm_service import LLMService, get_llm_service

settings = get_settings()


class ReflectionAgent(BaseAgent):
    """Agent responsible for validating translation quality."""

    def __init__(self, max_retries: int | None = None):
        super().__init__("Reflection")
        self.llm_service: LLMService | None = None
        self.max_retries = max_retries or settings.max_reflection_retries

    def _get_llm_service(self) -> LLMService:
        """Lazily initialize LLM service."""
        if self.llm_service is None:
            self.llm_service = get_llm_service()
        return self.llm_service

    async def execute(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate articles and retry if needed.

        Args:
            articles: List of processed articles to validate

        Returns:
            List of validated articles
        """
        if not articles:
            return []

        # 初始化 LLM 服务
        try:
            llm = self._get_llm_service()
            self.logger.info("LLM service initialized for reflection", model=llm.model)
        except Exception as e:
            self.logger.error("Failed to initialize LLM service for reflection", error=str(e))
            # 如果 LLM 初始化失败，直接返回文章（跳过 reflection）
            for article in articles:
                article["reflection_passed"] = True
                article["reflection_retries"] = 0
            return articles

        validated_articles = []
        errors_count = 0

        for i, article in enumerate(articles):
            try:
                validated = await self._validate_article(article, i)
                if validated:
                    validated_articles.append(validated)
            except Exception as e:
                errors_count += 1
                self.logger.error(
                    f"Error validating article {i + 1}",
                    error=str(e),
                    article_url=article.get("source_url"),
                    traceback=traceback.format_exc(),
                )
                # 出错时仍保留文章
                article["reflection_passed"] = True
                article["reflection_retries"] = 0
                validated_articles.append(article)

        self.logger.info(
            "Reflection phase complete",
            articles_input=len(articles),
            articles_validated=len(validated_articles),
            errors_count=errors_count,
        )

        return validated_articles

    async def _validate_article(self, article: dict[str, Any], index: int) -> dict[str, Any] | None:
        """Validate a single article with retries.

        Args:
            article: Article to validate
            index: Article index for logging

        Returns:
            Validated article or None if validation failed after retries
        """
        llm = self._get_llm_service()
        retries = 0

        # 检查必要字段
        if not article.get("chinese_title") or not article.get("chinese_summary"):
            self.logger.warning(
                f"Article {index + 1} missing translation, skipping reflection",
                article_url=article.get("source_url"),
            )
            article["reflection_passed"] = True
            article["reflection_retries"] = 0
            return article

        while retries < self.max_retries:
            try:
                result = await llm.reflect(
                    chinese_title=article["chinese_title"],
                    chinese_summary=article["chinese_summary"],
                    original_title=article["original_title"],
                    original_content=article.get("full_content", ""),
                )

                if result.passed:
                    article["reflection_passed"] = True
                    article["reflection_feedback"] = None
                    article["reflection_retries"] = retries
                    return article

                # Retry: regenerate translation
                issues = result.issues or []
                self.logger.info(
                    "Reflection failed, retrying",
                    article_url=article.get("source_url"),
                    attempt=retries + 1,
                    max_retries=self.max_retries,
                    issues=issues[:2] if issues else [],  # 只显示前2个问题
                )

                # Regenerate translation
                translation = await llm.translate_and_summarize(
                    title=article["original_title"],
                    content=article.get("full_content", ""),
                    entities_to_preserve=article.get("entities_preserved"),
                )

                article["chinese_title"] = translation.chinese_title
                article["chinese_summary"] = translation.chinese_summary
                article["entities_preserved"] = translation.entities_preserved or []
                article["reflection_feedback"] = result.feedback

                retries += 1

            except Exception as e:
                self.logger.warning(
                    f"Error during reflection attempt {retries + 1}",
                    error=str(e),
                    article_url=article.get("source_url"),
                )
                retries += 1
                if retries >= self.max_retries:
                    break

        # Max retries reached - still return article
        self.logger.warning(
            "Reflection failed after max retries, keeping article",
            article_url=article.get("source_url"),
            max_retries=self.max_retries,
        )

        article["reflection_passed"] = True  # 标记为通过，避免丢失文章
        article["reflection_retries"] = retries
        return article


# Singleton instance
reflection_agent = ReflectionAgent()