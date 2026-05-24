"""Decision CRUD endpoints."""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Decision
from db_utils import get_db

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.get("/{repo_id}")
async def list_decisions(
    repo_id: int,
    decision_type: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Decision).where(Decision.repo_id == repo_id)
    if decision_type:
        stmt = stmt.where(Decision.decision_type == decision_type)
    stmt = stmt.order_by(Decision.occurred_at.desc().nullslast()).limit(limit)
    result = await db.execute(stmt)
    return [_decision_dict(d) for d in result.scalars().all()]


@router.get("/detail/{decision_id}")
async def get_decision(decision_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Decision).where(Decision.id == decision_id))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Decision not found")
    return _decision_dict(d)


def _decision_dict(d: Decision) -> dict:
    tags = []
    try:
        tags = json.loads(d.tags or "[]")
    except Exception:
        pass
    return {
        "id": d.id,
        "repo_id": d.repo_id,
        "title": d.title,
        "summary": d.summary,
        "decision_type": d.decision_type,
        "rationale": d.rationale,
        "confidence_score": d.confidence_score,
        "tags": tags,
        "occurred_at": d.occurred_at.isoformat() if d.occurred_at else None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }
