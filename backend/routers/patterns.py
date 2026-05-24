"""Failure pattern detection endpoints."""
import json
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import FailurePattern, Repository
from db_utils import get_db
from hermes_session import get_hermes_client
from services.pattern_detector import detect_patterns

router = APIRouter(prefix="/api/patterns", tags=["patterns"])


@router.get("/{repo_id}")
async def list_patterns(repo_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FailurePattern)
        .where(FailurePattern.repo_id == repo_id)
        .order_by(FailurePattern.detected_at.desc())
    )
    return [_pattern_dict(p) for p in result.scalars().all()]


@router.post("/analyze/{repo_id}")
async def analyze_patterns(
    repo_id: int,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    background.add_task(_run_pattern_analysis, repo_id)
    return {"status": "analysis_started"}


async def _run_pattern_analysis(repo_id: int):
    from db_utils import _AsyncSessionLocal  # noqa: PLC0415

    async with _AsyncSessionLocal() as db:
        result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = result.scalar_one_or_none()
        if repo:
            hermes = get_hermes_client()
            await detect_patterns(db, repo, hermes)


def _pattern_dict(p: FailurePattern) -> dict:
    related = []
    try:
        related = json.loads(p.related_decision_ids or "[]")
    except Exception:
        pass
    return {
        "id": p.id,
        "repo_id": p.repo_id,
        "pattern_name": p.pattern_name,
        "description": p.description,
        "severity": p.severity,
        "occurrences": p.occurrences,
        "first_seen": p.first_seen.isoformat() if p.first_seen else None,
        "last_seen": p.last_seen.isoformat() if p.last_seen else None,
        "related_decision_ids": related,
        "detected_at": p.detected_at.isoformat() if p.detected_at else None,
    }
