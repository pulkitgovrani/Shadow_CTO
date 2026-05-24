"""Core ingestion pipeline: GitHub events → Hermes persistent memory → SQLite decisions."""
import json
import re
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Decision, RawEvent, Repository
from hermes_client import HermesClient

INGEST_SYSTEM_PROMPT = """You are the Shadow CTO for {repo_name}. You have been observing this repository's history to build an institutional memory of engineering decisions.

When you receive a commit, PR, or issue, your job is to:
1. Determine if a meaningful engineering decision was made
2. Extract the rationale (why it was done, what problem it solved)
3. Classify the decision type
4. Remember this for future questions

Always respond in this exact JSON format:
{{
  "is_decision": true or false,
  "title": "concise decision title (max 10 words)",
  "decision_type": "one of: addition|removal|refactor|rollback|migration|security|performance|config",
  "rationale": "why was this done? what problem did it solve?",
  "impact": "what changed as a result?",
  "tags": ["tag1", "tag2"],
  "confidence": 0.0 to 1.0
}}

If no meaningful decision was made (e.g., typo fix, dependency bump), set is_decision to false."""


def _format_event(event_type: str, data: dict) -> str:
    if event_type == "commit":
        files = ", ".join(data.get("files_changed", [])[:5])
        return (
            f"COMMIT by {data.get('author')} on {data.get('date', '')[:10]}\n"
            f"Message: {data.get('message', '')[:500]}\n"
            f"Files changed: {files}\n"
            f"+{data.get('additions', 0)} -{data.get('deletions', 0)} lines\n"
            f"URL: {data.get('url', '')}"
        )
    elif event_type == "pr":
        status = "MERGED" if data.get("merged") else "CLOSED"
        labels = ", ".join(data.get("labels", []))
        return (
            f"PULL REQUEST #{data.get('number')} [{status}] by {data.get('author')}\n"
            f"Title: {data.get('title', '')}\n"
            f"Description: {data.get('body', '')[:800]}\n"
            f"Labels: {labels}\n"
            f"URL: {data.get('url', '')}"
        )
    else:  # issue
        labels = ", ".join(data.get("labels", []))
        return (
            f"ISSUE #{data.get('number')} [CLOSED] by {data.get('author')}\n"
            f"Title: {data.get('title', '')}\n"
            f"Description: {data.get('body', '')[:800]}\n"
            f"Labels: {labels}\n"
            f"URL: {data.get('url', '')}"
        )


def _extract_json(text: str) -> dict | None:
    """Pull JSON from LLM response even if wrapped in markdown fences."""
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


async def ingest_events(
    db: AsyncSession,
    repo: Repository,
    raw_events: list[dict],
    hermes: HermesClient,
) -> list[Decision]:
    """Store raw events and feed them to Hermes, extracting decisions."""
    decisions_created: list[Decision] = []
    repo_display = f"{repo.owner}/{repo.name}"

    for event in raw_events:
        event_type = event["event_type"]
        external_id = event["external_id"]
        data = event["data"]

        # Check if already stored
        existing = await db.execute(
            select(RawEvent).where(
                RawEvent.repo_id == repo.id,
                RawEvent.event_type == event_type,
                RawEvent.external_id == external_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Store raw event
        raw = RawEvent(
            repo_id=repo.id,
            event_type=event_type,
            external_id=external_id,
            payload=json.dumps(data),
        )
        db.add(raw)
        await db.flush()

        # Send to Hermes for decision extraction
        formatted = _format_event(event_type, data)
        messages = [
            {
                "role": "system",
                "content": INGEST_SYSTEM_PROMPT.format(repo_name=repo_display),
            },
            {
                "role": "user",
                "content": f"New {event_type.upper()} to analyze:\n\n{formatted}",
            },
        ]

        try:
            response = await hermes.chat(
                messages=messages,
                session_id=repo.hermes_session_id,
                temperature=0.2,
            )
            parsed = _extract_json(response)
        except Exception:
            parsed = None

        if parsed and parsed.get("is_decision"):
            occurred_at = None
            if event_type == "commit" and data.get("date"):
                try:
                    occurred_at = datetime.fromisoformat(data["date"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            elif event_type == "pr" and data.get("merged_at"):
                try:
                    occurred_at = datetime.fromisoformat(data["merged_at"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            decision = Decision(
                repo_id=repo.id,
                title=parsed.get("title", "Unknown decision"),
                summary=parsed.get("impact", ""),
                decision_type=parsed.get("decision_type", "other"),
                rationale=parsed.get("rationale", ""),
                linked_events=json.dumps([raw.id]),
                confidence_score=float(parsed.get("confidence", 0.5)),
                tags=json.dumps(parsed.get("tags", [])),
                occurred_at=occurred_at,
            )
            db.add(decision)
            decisions_created.append(decision)

        raw.processed = True

    await db.commit()
    return decisions_created
