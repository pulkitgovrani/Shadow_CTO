"""GitHub sync endpoint — fetches new events and feeds them to Hermes."""
import logging
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

from database import Repository
from db_utils import get_db
from hermes_session import get_hermes_client
from services.github_service import fetch_repo_events
from services.ingestion import ingest_events

router = APIRouter(prefix="/api/sync", tags=["sync"])

_sync_status: dict[int, dict] = {}


@router.post("/{repo_id}")
async def trigger_sync(
    repo_id: int,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if _sync_status.get(repo_id, {}).get("running"):
        return {"status": "already_running"}

    log.info("🔄 Sync started for %s/%s", repo.owner, repo.name)
    background.add_task(_do_sync, repo_id)
    return {"status": "started", "repo_id": repo_id}


@router.get("/{repo_id}/status")
async def sync_status(repo_id: int):
    return _sync_status.get(repo_id, {"status": "never_run"})


async def _do_sync(repo_id: int):
    """Background task: fetch GitHub events and ingest into Hermes."""
    from db_utils import _AsyncSessionLocal  # noqa: PLC0415 — lazy import inside bg task

    _sync_status[repo_id] = {"running": True, "started_at": datetime.utcnow().isoformat()}

    async with _AsyncSessionLocal() as db:
        result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = result.scalar_one_or_none()
        if not repo:
            _sync_status[repo_id] = {"running": False, "error": "repo not found"}
            return

        try:
            log.info("📡 Fetching GitHub events for %s/%s ...", repo.owner, repo.name)
            events = fetch_repo_events(
                owner=repo.owner,
                name=repo.name,
                since=repo.last_sync_at,
            )
            log.info("✅ Fetched %d events — ingesting into Hermes memory ...", len(events))
            hermes = get_hermes_client()
            new_decisions = await ingest_events(db, repo, events, hermes)

            repo.last_sync_at = datetime.utcnow()
            await db.commit()

            log.info("🧠 Ingestion complete — %d new decisions extracted", len(new_decisions))
            _sync_status[repo_id] = {
                "running": False,
                "last_run": datetime.utcnow().isoformat(),
                "events_fetched": len(events),
                "decisions_extracted": len(new_decisions),
            }
        except Exception as exc:
            log.error("❌ Sync failed for repo %d: %s", repo_id, exc)
            _sync_status[repo_id] = {
                "running": False,
                "error": str(exc),
                "last_run": datetime.utcnow().isoformat(),
            }
