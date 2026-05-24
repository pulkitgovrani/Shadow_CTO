"""Seed demo data — adds pre-built decisions so the UI looks great without a live GitHub sync."""
import asyncio
import json
import uuid
from datetime import datetime, timedelta

from database import Base, Decision, FailurePattern, Repository
from db_utils import get_engine, init_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./shadow_cto.db"

DEMO_DECISIONS = [
    {
        "title": "Remove Redis caching layer",
        "decision_type": "removal",
        "rationale": "Redis was causing OOM errors on the $5 DigitalOcean droplet. Switched to functools.lru_cache since we have fewer than 50 concurrent users.",
        "summary": "Replaced Redis with in-memory LRU cache, reducing infrastructure cost and eliminating memory crashes.",
        "confidence_score": 0.92,
        "tags": ["performance", "infrastructure", "cost"],
        "days_ago": 45,
    },
    {
        "title": "Migrate from JWT to session-based auth",
        "decision_type": "migration",
        "rationale": "JWT tokens were being stored in localStorage, which legal flagged as a GDPR compliance risk. Session cookies with HttpOnly flag are now used.",
        "summary": "Replaced JWT with server-side sessions to meet GDPR storage requirements.",
        "confidence_score": 0.97,
        "tags": ["security", "gdpr", "auth"],
        "days_ago": 120,
    },
    {
        "title": "Switch ORM from SQLAlchemy to Tortoise",
        "decision_type": "refactor",
        "rationale": "SQLAlchemy's async support in v1.4 was experimental and causing transaction deadlocks. Tortoise ORM had better native async support at the time.",
        "summary": "Migrated all database models and queries to Tortoise ORM for reliable async operation.",
        "confidence_score": 0.85,
        "tags": ["database", "async", "orm"],
        "days_ago": 200,
    },
    {
        "title": "Rollback Tortoise ORM — return to SQLAlchemy 2.0",
        "decision_type": "rollback",
        "rationale": "Tortoise had poor migration tooling and no Alembic support. After SQLAlchemy 2.0 released with proper async, we migrated back. The Tortoise experiment cost 2 sprints.",
        "summary": "Reverted to SQLAlchemy 2.0 which now has stable async support and full Alembic integration.",
        "confidence_score": 0.95,
        "tags": ["database", "orm", "rollback"],
        "days_ago": 60,
    },
    {
        "title": "Add rate limiting to public API endpoints",
        "decision_type": "security",
        "rationale": "A scraper was hitting /api/search 40,000 times per hour, causing $180 in unexpected Anthropic API costs. Added slowapi rate limiting at 60 req/min per IP.",
        "summary": "Implemented rate limiting on all public endpoints to prevent API cost abuse.",
        "confidence_score": 0.99,
        "tags": ["security", "rate-limiting", "cost"],
        "days_ago": 30,
    },
    {
        "title": "Extract email service into separate microservice",
        "decision_type": "refactor",
        "rationale": "Email sending was blocking the main request thread during high-volume campaigns. Extracted to a dedicated worker process with a Redis queue.",
        "summary": "Moved email delivery to an async worker service to prevent P99 latency spikes.",
        "confidence_score": 0.88,
        "tags": ["performance", "microservice", "email"],
        "days_ago": 90,
    },
    {
        "title": "Add database connection pooling",
        "decision_type": "performance",
        "rationale": "Production was exhausting PostgreSQL connections during traffic spikes (seen 3 times in 2 months). Added pgBouncer connection pooling with pool_size=20.",
        "summary": "Implemented connection pooling to prevent connection exhaustion under load.",
        "confidence_score": 0.93,
        "tags": ["database", "performance", "postgresql"],
        "days_ago": 15,
    },
    {
        "title": "Replace Celery with ARQ for background tasks",
        "decision_type": "removal",
        "rationale": "Celery required a separate broker (RabbitMQ), adding operational complexity. ARQ uses Redis (already in stack) and has a simpler API. Reduced infrastructure by one service.",
        "summary": "Removed Celery + RabbitMQ, replaced with ARQ + Redis for background task processing.",
        "confidence_score": 0.87,
        "tags": ["infrastructure", "background-tasks", "simplification"],
        "days_ago": 75,
    },
]

DEMO_PATTERNS = [
    {
        "pattern_name": "Repeated ORM migration failures",
        "description": "The codebase switched ORMs twice (SQLAlchemy → Tortoise → SQLAlchemy) within 8 months, costing 3+ sprints. Each switch was caused by discovering migration tooling limitations only after full adoption.",
        "severity": "high",
        "occurrences": 2,
    },
    {
        "pattern_name": "Connection pool exhaustion under load",
        "description": "Database connection limits were hit 3 times before connection pooling was added. The fix was known but deprioritized. Consider adding this to the new service checklist.",
        "severity": "medium",
        "occurrences": 3,
    },
    {
        "pattern_name": "Infrastructure cost surprises from external APIs",
        "description": "Unexpected API costs appeared twice (Redis OOM, Anthropic scraper). No cost alerting was in place either time. Suggest adding budget alerts to all external service integrations.",
        "severity": "medium",
        "occurrences": 2,
    },
]


async def seed():
    init_db(DATABASE_URL)
    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as db:
        # Create demo repo
        repo = Repository(
            owner="acmecorp",
            name="platform-api",
            github_url="https://github.com/acmecorp/platform-api",
            hermes_session_id=str(uuid.uuid4()),
            last_sync_at=datetime.utcnow(),
            created_at=datetime.utcnow() - timedelta(days=250),
        )
        db.add(repo)
        await db.flush()

        now = datetime.utcnow()
        for d in DEMO_DECISIONS:
            decision = Decision(
                repo_id=repo.id,
                title=d["title"],
                decision_type=d["decision_type"],
                rationale=d["rationale"],
                summary=d["summary"],
                confidence_score=d["confidence_score"],
                tags=json.dumps(d["tags"]),
                linked_events=json.dumps([]),
                occurred_at=now - timedelta(days=d["days_ago"]),
            )
            db.add(decision)

        for p in DEMO_PATTERNS:
            pattern = FailurePattern(
                repo_id=repo.id,
                pattern_name=p["pattern_name"],
                description=p["description"],
                severity=p["severity"],
                occurrences=p["occurrences"],
                first_seen=now - timedelta(days=200),
                last_seen=now - timedelta(days=15),
                related_decision_ids=json.dumps([]),
            )
            db.add(pattern)

        await db.commit()
        print(f"Demo data seeded! Repo ID: {repo.id}")
        print(f"Added {len(DEMO_DECISIONS)} decisions and {len(DEMO_PATTERNS)} patterns.")


if __name__ == "__main__":
    asyncio.run(seed())
