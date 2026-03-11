"""APScheduler-based workflow scheduler for daily news aggregation."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from app.config import get_settings
from app.core import get_logger
from app.models.database import async_session_factory
from app.workflow.graph import run_workflow

logger = get_logger(__name__)

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None


async def run_scheduled_workflow() -> None:
    """Execute the workflow as a scheduled job.

    This function creates its own database session and handles all errors
    to prevent the scheduler from crashing.
    """
    logger.info("Starting scheduled workflow run")

    try:
        async with async_session_factory() as session:
            result = await run_workflow(session)

            logger.info(
                "Scheduled workflow completed",
                articles_stored=result.get("total_articles_stored", 0),
                errors=len(result.get("errors", [])),
            )

    except Exception as e:
        logger.error("Scheduled workflow failed", error=str(e), exc_info=True)


def start_scheduler() -> None:
    """Initialize and start the scheduler.

    Configures a daily cron job to run the workflow at the configured time.
    """
    global _scheduler

    settings = get_settings()

    if not settings.scheduler_enabled:
        logger.info("Scheduler is disabled, skipping startup")
        return

    if _scheduler is not None:
        logger.warning("Scheduler already running, skipping startup")
        return

    # Create scheduler with timezone support
    tz = timezone(settings.scheduler_timezone)
    _scheduler = AsyncIOScheduler(timezone=tz)

    # Add the daily job
    trigger = CronTrigger(
        hour=settings.scheduler_hour,
        minute=settings.scheduler_minute,
        timezone=tz,
    )

    _scheduler.add_job(
        run_scheduled_workflow,
        trigger=trigger,
        id="daily_workflow",
        name="Daily News Aggregation Workflow",
        replace_existing=True,
    )

    _scheduler.start()

    logger.info(
        "Scheduler started",
        timezone=settings.scheduler_timezone,
        hour=settings.scheduler_hour,
        minute=settings.scheduler_minute,
        next_run=_scheduler.get_jobs()[0].next_run_time.isoformat() if _scheduler.get_jobs() else None,
    )


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=True)
        _scheduler = None
        logger.info("Scheduler shut down")


def get_scheduler() -> AsyncIOScheduler | None:
    """Get the current scheduler instance."""
    return _scheduler