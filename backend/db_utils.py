"""Async SQLAlchemy engine and session factory."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

_engine = None
_AsyncSessionLocal = None


def init_db(database_url: str):
    global _engine, _AsyncSessionLocal
    _engine = create_async_engine(database_url, echo=False)
    _AsyncSessionLocal = sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )


def get_engine():
    return _engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
