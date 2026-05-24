"""Autonomous failure pattern detection via Hermes."""
import json
import re
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Decision, FailurePattern, Repository
from hermes_client import HermesClient

PATTERN_SYSTEM_PROMPT = """You are the Shadow CTO for {repo_name}.
You have been tracking this repository's engineering history.

Review the decisions below and identify recurring failure patterns:
- Components that keep getting reverted or re-done
- Performance issues that reappear
- Security problems addressed multiple times
- Architecture decisions that were later reversed
- Dependencies causing repeated friction

Respond with JSON:
{{
  "patterns": [
    {{
      "name": "short pattern name",
      "description": "what keeps happening and why it's a concern",
      "severity": "low|medium|high",
      "related_decision_titles": ["title1", "title2"]
    }}
  ]
}}

If no clear patterns exist, return {{"patterns": []}}."""


async def detect_patterns(
    db: AsyncSession,
    repo: Repository,
    hermes: HermesClient,
) -> list[FailurePattern]:
    """Ask Hermes to analyze all known decisions and identify patterns."""
    result = await db.execute(
        select(Decision).where(Decision.repo_id == repo.id).order_by(Decision.occurred_at)
    )
    decisions = result.scalars().all()

    if len(decisions) < 3:
        return []

    decisions_text = "\n\n".join(
        f"[{d.decision_type.upper()}] {d.title}\n  Rationale: {d.rationale}"
        for d in decisions
    )

    messages = [
        {
            "role": "system",
            "content": PATTERN_SYSTEM_PROMPT.format(repo_name=f"{repo.owner}/{repo.name}"),
        },
        {
            "role": "user",
            "content": f"Engineering decisions for {repo.owner}/{repo.name}:\n\n{decisions_text}\n\nIdentify recurring failure patterns.",
        },
    ]

    try:
        response = await hermes.chat(
            messages=messages,
            session_id=repo.hermes_session_id,
            temperature=0.3,
        )
        match = re.search(r"\{[\s\S]*\}", response)
        parsed = json.loads(match.group()) if match else {"patterns": []}
    except Exception:
        return []

    patterns_created = []
    now = datetime.utcnow()

    for p in parsed.get("patterns", []):
        # Find related decisions
        related_ids = []
        for d in decisions:
            for title in p.get("related_decision_titles", []):
                if title.lower() in d.title.lower():
                    related_ids.append(d.id)

        pattern = FailurePattern(
            repo_id=repo.id,
            pattern_name=p.get("name", "Unknown pattern"),
            description=p.get("description", ""),
            severity=p.get("severity", "medium"),
            occurrences=len(related_ids),
            first_seen=now,
            last_seen=now,
            related_decision_ids=json.dumps(related_ids),
        )
        db.add(pattern)
        patterns_created.append(pattern)

    await db.commit()
    return patterns_created
