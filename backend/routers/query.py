"""Natural language Q&A endpoint — streams Hermes answers via SSE."""
import logging
from fastapi import APIRouter, Depends, HTTPException

log = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Repository
from db_utils import get_db
from hermes_session import get_hermes_client

router = APIRouter(prefix="/api/query", tags=["query"])

QUERY_SYSTEM = """You are the Shadow CTO for {repo_name}. You have extensive institutional memory of every engineering decision made in this codebase — the commits, pull requests, issues, and the reasoning behind each one.

When answering questions:
- Be specific: cite commit messages, PR titles, issue numbers, and dates when you know them
- Explain the WHY, not just the what
- If you notice patterns or risks, mention them
- If you don't have information on something, say so clearly

Answer as an experienced engineering leader who has been closely watching this codebase."""


class QueryRequest(BaseModel):
    repo_id: int
    question: str


@router.post("")
async def query(body: QueryRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == body.repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    hermes = get_hermes_client()
    messages = [
        {
            "role": "system",
            "content": QUERY_SYSTEM.format(repo_name=f"{repo.owner}/{repo.name}"),
        },
        {"role": "user", "content": body.question},
    ]

    log.info("💬 Query received for %s/%s: %s", repo.owner, repo.name, body.question)

    async def generate():
        log.info("🤖 Streaming response from Hermes (model: gemma4:e4b) ...")
        try:
            async for chunk in hermes.stream_chat(
                messages=messages,
                session_id=repo.hermes_session_id,
            ):
                escaped = chunk.replace("\n", "\\n")
                yield f"data: {escaped}\n\n"
        except Exception as exc:
            log.error("❌ Stream error: %s", exc)
            yield f"data: [ERROR] {exc}\n\n"
        log.info("✅ Stream complete")
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

# Date-range filter: ?since=YYYY-MM-DD&until=YYYY-MM-DD narrows Q&A to a time window
