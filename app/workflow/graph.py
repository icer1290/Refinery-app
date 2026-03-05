"""LangGraph workflow graph construction."""

import uuid
from datetime import datetime, timezone
from typing import Literal

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger
from app.models.orm_models import WorkflowRun
from app.workflow.nodes import (
    dedup_node,
    reflection_node,
    scoring_node,
    scout_node,
    storage_node,
    update_workflow_run,
    writing_node,
)
from app.workflow.state import WorkflowState, create_initial_state

logger = get_logger(__name__)


def create_workflow_graph():
    """Create the news aggregation workflow graph.

    Returns:
        Compiled LangGraph workflow
    """
    # Create the graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("scout", scout_node)
    workflow.add_node("dedup", dedup_node)
    workflow.add_node("scoring", scoring_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("storage", storage_node)

    # Define edges
    workflow.set_entry_point("scout")
    workflow.add_edge("scout", "dedup")
    workflow.add_edge("dedup", "scoring")
    workflow.add_edge("scoring", "writing")
    workflow.add_edge("writing", "reflection")
    workflow.add_edge("reflection", "storage")
    workflow.add_edge("storage", END)

    return workflow.compile()


def should_continue(state: WorkflowState) -> Literal["continue", "end"]:
    """Determine if workflow should continue.

    Args:
        state: Current workflow state

    Returns:
        "continue" or "end"
    """
    # Check for critical errors
    if state["current_phase"].endswith("_failed"):
        if "scout" in state["current_phase"]:
            return "end"  # No articles to process
    return "continue"


async def run_workflow(
    session: AsyncSession,
    feed_urls: list[str] | None = None,
    score_threshold: float | None = None,
    force_reprocess: bool = False,
) -> WorkflowState:
    """Execute the news aggregation workflow.

    Args:
        session: Database session
        feed_urls: Specific RSS feeds to fetch (optional)
        score_threshold: Override score threshold (optional)
        force_reprocess: Force reprocessing existing articles

    Returns:
        Final workflow state
    """
    # Create workflow run record
    run_id = str(uuid.uuid4())
    workflow_run = WorkflowRun(
        id=uuid.UUID(run_id),
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    session.add(workflow_run)
    await session.flush()

    logger.info(
        "Starting workflow run",
        run_id=run_id,
        feed_count=len(feed_urls) if feed_urls else "default",
    )

    # Create initial state
    state = create_initial_state(
        run_id=run_id,
        feed_urls=feed_urls,
        score_threshold=score_threshold,
        force_reprocess=force_reprocess,
    )

    # Create and run the graph
    graph = create_workflow_graph()

    try:
        # Execute nodes sequentially with session injection
        # Note: LangGraph doesn't natively support session injection,
        # so we execute nodes manually

        # Scout phase
        state.update(await scout_node(state))

        if should_continue(state) == "end":
            await update_workflow_run(session, run_id, state, "failed")
            return state

        # Dedup phase
        state.update(await dedup_node(state, session))

        if should_continue(state) == "end":
            await update_workflow_run(session, run_id, state, "failed")
            return state

        # Scoring phase
        state.update(await scoring_node(state))

        if should_continue(state) == "end":
            await update_workflow_run(session, run_id, state, "failed")
            return state

        # Writing phase
        state.update(await writing_node(state))

        if should_continue(state) == "end":
            await update_workflow_run(session, run_id, state, "failed")
            return state

        # Reflection phase
        state.update(await reflection_node(state))

        if should_continue(state) == "end":
            await update_workflow_run(session, run_id, state, "failed")
            return state

        # Storage phase
        state.update(await storage_node(state, session))

        # Update workflow run status
        status = "completed" if not state["errors"] else "completed_with_errors"
        await update_workflow_run(session, run_id, state, status)

        logger.info(
            "Workflow run completed",
            run_id=run_id,
            status=status,
            articles_stored=state["total_articles_stored"],
        )

        return state

    except Exception as e:
        logger.error("Workflow run failed", run_id=run_id, error=str(e))
        await update_workflow_run(session, run_id, state, "failed")
        raise