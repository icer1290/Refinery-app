"""Workflow node implementations."""

import uuid
from datetime import datetime, timezone
from typing import Any

from langgraph.runtime import Runtime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.reflection_agent import reflection_agent
from app.agents.scorer_agent import scorer_agent
from app.agents.scout_agent import scout_agent
from app.agents.writer_agent import writer_agent
from app.config import get_settings
from app.core import get_logger
from app.models.orm_models import NewsArticle, WorkflowRun
from app.services.vector_store import vector_store
from app.workflow.context import WorkflowContext
from app.workflow.state import (
    ArticleCandidate,
    WorkflowError,
    WorkflowState,
)

logger = get_logger(__name__)
settings = get_settings()


async def scout_node(state: WorkflowState) -> dict[str, Any]:
    """Fetch articles from RSS feeds.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info("Starting scout phase", run_id=state["run_id"])

    try:
        # Fetch articles from feeds
        articles = await scout_agent.execute(state.get("feed_urls"))

        # Update statistics
        total_feeds = len(state.get("feed_urls") or settings.default_rss_feeds)

        return {
            "raw_articles": articles,
            "current_phase": "scout_complete",
            "total_feeds_fetched": total_feeds,
            "total_articles_found": len(articles),
        }

    except Exception as e:
        logger.error("Scout phase failed", error=str(e))
        return {
            "errors": [WorkflowError(
                phase="scout",
                message=str(e),
                details={"error_type": type(e).__name__},
            )],
            "current_phase": "scout_failed",
        }


async def dedup_node(
    state: WorkflowState,
    runtime: Runtime[WorkflowContext],
) -> dict[str, Any]:
    """Deduplicate articles using content hash and URL.

    Note: Semantic deduplication with embeddings is disabled for now
    due to API compatibility issues with DashScope.

    Args:
        state: Current workflow state
        runtime: LangGraph runtime with WorkflowContext

    Returns:
        Updated state fields
    """
    logger.info("Starting dedup phase", run_id=state["run_id"])

    # Extract session from context
    session = runtime.context.session

    articles = state["raw_articles"]
    if not articles:
        return {
            "deduplicated_articles": [],
            "current_phase": "dedup_complete",
            "total_articles_after_dedup": 0,
        }

    deduplicated = []
    seen_hashes = set()
    seen_urls = set()

    for article in articles:
        # Check hash-based duplicate
        if article["content_hash"] in seen_hashes:
            logger.debug(
                "Skipped hash duplicate",
                title=article["original_title"][:50],
            )
            continue

        # Check URL-based duplicate
        if article["source_url"] in seen_urls:
            logger.debug(
                "Skipped URL duplicate",
                url=article["source_url"],
            )
            continue

        # Check database for existing articles
        if not state.get("force_reprocess", False):
            existing = await vector_store.check_duplicate_by_url(
                session, article["source_url"]
            )
            if existing:
                logger.debug(
                    "Skipped existing article",
                    url=article["source_url"],
                )
                continue

        # Add to deduplicated list
        deduplicated.append(article)
        seen_hashes.add(article["content_hash"])
        seen_urls.add(article["source_url"])

    logger.info(
        "Dedup phase complete",
        input_count=len(articles),
        output_count=len(deduplicated),
    )

    return {
        "deduplicated_articles": deduplicated,
        "current_phase": "dedup_complete",
        "total_articles_after_dedup": len(deduplicated),
    }


async def scoring_node(state: WorkflowState) -> dict[str, Any]:
    """Score articles and filter by threshold.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info("Starting scoring phase", run_id=state["run_id"])

    articles = state["deduplicated_articles"]
    if not articles:
        return {
            "scored_articles": [],
            "current_phase": "scoring_complete",
            "total_articles_after_scoring": 0,
        }

    # Use custom threshold if provided
    threshold = state.get("score_threshold") or settings.score_threshold

    try:
        scored = await scorer_agent.execute(articles)

        # Apply custom threshold
        filtered = [a for a in scored if (a.get("total_score") or 0) >= threshold]

        return {
            "scored_articles": filtered,
            "current_phase": "scoring_complete",
            "total_articles_after_scoring": len(filtered),
        }

    except Exception as e:
        logger.error("Scoring phase failed", error=str(e))
        return {
            "errors": [WorkflowError(
                phase="scoring",
                message=str(e),
                details={"error_type": type(e).__name__},
            )],
            "current_phase": "scoring_failed",
            "scored_articles": [],
            "total_articles_after_scoring": 0,
        }


async def writing_node(state: WorkflowState) -> dict[str, Any]:
    """Extract content and generate translations.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info("Starting writing phase", run_id=state["run_id"])

    articles = state["scored_articles"]
    if not articles:
        return {
            "processed_articles": [],
            "current_phase": "writing_complete",
        }

    try:
        processed = await writer_agent.execute(articles)
        return {
            "processed_articles": processed,
            "current_phase": "writing_complete",
        }

    except Exception as e:
        logger.error("Writing phase failed", error=str(e))
        return {
            "errors": [WorkflowError(
                phase="writing",
                message=str(e),
                details={"error_type": type(e).__name__},
            )],
            "current_phase": "writing_failed",
            "processed_articles": [],
        }


async def reflection_node(state: WorkflowState) -> dict[str, Any]:
    """Validate translations and retry if needed.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info("Starting reflection phase", run_id=state["run_id"])

    articles = state["processed_articles"]
    if not articles:
        return {
            "final_articles": [],
            "current_phase": "reflection_complete",
        }

    try:
        validated = await reflection_agent.execute(articles)
        return {
            "final_articles": validated,
            "current_phase": "reflection_complete",
        }

    except Exception as e:
        logger.error("Reflection phase failed", error=str(e))
        return {
            "errors": [WorkflowError(
                phase="reflection",
                message=str(e),
                details={"error_type": type(e).__name__},
            )],
            "current_phase": "reflection_failed",
            "final_articles": [],
        }


async def storage_node(
    state: WorkflowState,
    runtime: Runtime[WorkflowContext],
) -> dict[str, Any]:
    """Store articles to database.

    Args:
        state: Current workflow state
        runtime: LangGraph runtime with WorkflowContext

    Returns:
        Updated state fields
    """
    logger.info("Starting storage phase", run_id=state["run_id"])

    # Extract session from context
    session = runtime.context.session

    articles = state["final_articles"]
    if not articles:
        return {
            "stored_article_ids": [],
            "current_phase": "storage_complete",
            "total_articles_stored": 0,
        }

    stored_ids = []

    for article in articles:
        try:
            # Create database record
            db_article = NewsArticle(
                source_name=article["source_name"],
                source_url=article["source_url"],
                original_title=article["original_title"],
                original_description=article.get("original_description"),
                chinese_title=article.get("chinese_title"),
                chinese_summary=article.get("chinese_summary"),
                full_content=article.get("full_content"),
                total_score=article.get("total_score"),
                industry_impact_score=article.get("industry_impact_score"),
                milestone_score=article.get("milestone_score"),
                attention_score=article.get("attention_score"),
                published_at=article.get("published_at"),
                reflection_retries=article.get("reflection_retries", 0),
                reflection_passed=article.get("reflection_passed", False),
                reflection_feedback=article.get("reflection_feedback"),
                is_published=True,
            )
            session.add(db_article)
            await session.flush()

            stored_ids.append(str(db_article.id))

        except Exception as e:
            logger.error(
                "Failed to store article",
                url=article.get("source_url"),
                error=str(e),
            )
            continue

    logger.info(
        "Storage phase complete",
        articles_stored=len(stored_ids),
    )

    return {
        "stored_article_ids": stored_ids,
        "current_phase": "storage_complete",
        "total_articles_stored": len(stored_ids),
    }


async def update_workflow_run(
    session: AsyncSession,
    run_id: str,
    state: WorkflowState,
    status: str,
) -> None:
    """Update workflow run record in database.

    Args:
        session: Database session
        run_id: Workflow run ID
        state: Current state
        status: New status
    """
    try:
        # Find workflow run
        stmt = select(WorkflowRun).where(WorkflowRun.id == uuid.UUID(run_id))
        result = await session.execute(stmt)
        workflow_run = result.scalar_one_or_none()

        if workflow_run:
            workflow_run.status = status
            workflow_run.completed_at = datetime.now(timezone.utc)
            workflow_run.total_feeds_fetched = state["total_feeds_fetched"]
            workflow_run.total_articles_found = state["total_articles_found"]
            workflow_run.total_articles_after_dedup = state["total_articles_after_dedup"]
            workflow_run.total_articles_after_scoring = state["total_articles_after_scoring"]
            workflow_run.total_articles_stored = state["total_articles_stored"]
            workflow_run.errors = [dict(e) for e in state["errors"]] if state["errors"] else None
            await session.flush()

    except Exception as e:
        logger.error("Failed to update workflow run", error=str(e))