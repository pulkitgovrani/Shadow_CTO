"""Repository management endpoints."""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Repository
from db_utils import get_db

router = APIRouter(prefix="/api/repos", tags=["repos"])


class RepoCreate(BaseModel):
    owner: str
    name: str


@router.post("", status_code=201)
async def create_repo(body: RepoCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Repository).where(
            Repository.owner == body.owner, Repository.name == body.name
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Repository already tracked")

    repo = Repository(
        owner=body.owner,
        name=body.name,
        github_url=f"https://github.com/{body.owner}/{body.name}",
        hermes_session_id=str(uuid.uuid4()),
        created_at=datetime.utcnow(),
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    return _repo_dict(repo)


@router.get("")
async def list_repos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).order_by(Repository.created_at.desc()))
    return [_repo_dict(r) for r in result.scalars().all()]


@router.get("/{repo_id}")
async def get_repo(repo_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return _repo_dict(repo)


def _repo_dict(r: Repository) -> dict:
    return {
        "id": r.id,
        "owner": r.owner,
        "name": r.name,
        "github_url": r.github_url,
        "last_sync_at": r.last_sync_at.isoformat() if r.last_sync_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
