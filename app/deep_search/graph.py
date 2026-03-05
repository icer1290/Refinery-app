"""Graph construction and execution for deep search workflow."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger
from app.deep_search.nodes import (
    conclude_node,
    fetch_article_node,
    reasoning_node,
    tools_node,
)
from app.deep_search.state import DeepSearchState, create_initial_deep_search_state

logger = get_logger(__name__)


async def run_deep_search(
    session: AsyncSession,
    article_id: str,
    max_iterations: int = 5,
) -> DeepSearchState:
    """Execute the deep search workflow.

    This function implements a manual ReAct loop following the pattern
    used in the existing workflow system.

    Args:
        session: Database session
        article_id: ID of the article to analyze
        max_iterations: Maximum number of ReAct iterations

    Returns:
        Final deep search state with report
    """
    logger.info(
        "Starting deep search",
        article_id=article_id,
        max_iterations=max_iterations,
    )

    # Create initial state
    state = create_initial_deep_search_state(
        article_id=article_id,
        max_iterations=max_iterations,
    )

    # Phase 1: Fetch article
    state.update(await fetch_article_node(state, session))

    if not state.get("article"):
        logger.error("Article not found, aborting deep search")
        return state

    # Phase 2: ReAct Loop
    while state["should_continue"] and state["current_iteration"] < state["max_iterations"]:
        # Reasoning step
        state.update(await reasoning_node(state))

        # Check if should continue
        if not state["should_continue"]:
            break

        # Tools execution step
        if state.get("_pending_action"):
            state.update(await tools_node(state, session))

    # Phase 3: Generate report
    state.update(await conclude_node(state))

    logger.info(
        "Deep search completed",
        article_id=article_id,
        iterations=state["current_iteration"],
        tools_used=len(state.get("tool_history", [])),
        errors=len(state.get("errors", [])),
    )

    return state