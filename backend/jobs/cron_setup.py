"""Register Hermes cron jobs and APScheduler periodic tasks on startup."""
import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from hermes_session import get_hermes_client

log = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def setup_jobs():
    """Called on FastAPI startup — registers both APScheduler and Hermes cron jobs."""
    global _scheduler
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8001")

    _scheduler = AsyncIOScheduler()

    # APScheduler: hourly GitHub sync for all tracked repos
    _scheduler.add_job(
        _hourly_sync_all_repos,
        "interval",
        hours=1,
        id="hourly_github_sync",
        replace_existing=True,
    )

    # APScheduler: daily pattern analysis at 2am
    _scheduler.add_job(
        _daily_pattern_analysis,
        "cron",
        hour=2,
        minute=0,
        id="daily_pattern_analysis",
        replace_existing=True,
    )

    _scheduler.start()
    log.info("APScheduler started with sync + pattern jobs")

    # Also register cron jobs in Hermes (shows in the Hermes jobs dashboard)
    hermes = get_hermes_client()

    await hermes.create_job(
        name="shadow-cto-hourly-sync",
        schedule="0 * * * *",
        prompt=(
            "You are the Shadow CTO. Remind yourself to process any new commits, "
            "PRs, and issues from watched repositories. The sync service at "
            f"{backend_url}/api/sync will handle the actual GitHub fetching."
        ),
    )

    await hermes.create_job(
        name="shadow-cto-daily-patterns",
        schedule="0 2 * * *",
        prompt=(
            "You are the Shadow CTO. Review the engineering decisions you have stored "
            "in your memory from the past 30 days. Identify any recurring failure "
            "patterns — components that keep breaking, decisions that get reversed, "
            "or technical debt accumulating. Prepare a concise pattern report."
        ),
    )

    log.info("Hermes cron jobs registered")


async def teardown_jobs():
    if _scheduler:
        _scheduler.shutdown(wait=False)


async def _hourly_sync_all_repos():
    from db_utils import _AsyncSessionLocal  # noqa: PLC0415
    from database import Repository  # noqa: PLC0415
    from routers.sync import _do_sync  # noqa: PLC0415

    async with _AsyncSessionLocal() as db:
        result = await db.execute(select(Repository))
        repos = result.scalars().all()

    for repo in repos:
        try:
            await _do_sync(repo.id)
        except Exception as exc:
            log.error("Sync failed for repo %d: %s", repo.id, exc)


async def _daily_pattern_analysis():
    from db_utils import _AsyncSessionLocal  # noqa: PLC0415
    from database import Repository  # noqa: PLC0415
    from services.pattern_detector import detect_patterns  # noqa: PLC0415

    hermes = get_hermes_client()

    async with _AsyncSessionLocal() as db:
        result = await db.execute(select(Repository))
        repos = result.scalars().all()

    for repo in repos:
        async with _AsyncSessionLocal() as db:
            try:
                await detect_patterns(db, repo, hermes)
            except Exception as exc:
                log.error("Pattern analysis failed for repo %d: %s", repo.id, exc)
