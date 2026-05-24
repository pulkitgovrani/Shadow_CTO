"""SQLAlchemy ORM models for Shadow CTO."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    github_url = Column(String, nullable=False)
    hermes_session_id = Column(String, default=lambda: str(uuid.uuid4()), nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RawEvent(Base):
    __tablename__ = "raw_events"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String, nullable=False)  # commit | pr | issue
    external_id = Column(String, nullable=False)
    payload = Column(Text, nullable=False)  # JSON
    processed = Column(Boolean, default=False)
    ingested_at = Column(DateTime, default=datetime.utcnow)


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text)
    decision_type = Column(String)  # addition|removal|refactor|rollback|migration|security|performance
    rationale = Column(Text)
    linked_events = Column(Text)  # JSON array of event IDs
    confidence_score = Column(Float, default=0.5)
    tags = Column(Text)  # JSON array
    occurred_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class FailurePattern(Base):
    __tablename__ = "failure_patterns"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, nullable=False, index=True)
    pattern_name = Column(String, nullable=False)
    description = Column(Text)
    occurrences = Column(Integer, default=1)
    severity = Column(String, default="medium")  # low|medium|high
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    related_decision_ids = Column(Text)  # JSON array
    detected_at = Column(DateTime, default=datetime.utcnow)
