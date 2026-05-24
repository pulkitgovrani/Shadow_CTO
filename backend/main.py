"""Shadow CTO — FastAPI application entry point."""
import logging
import os
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s — %(message)s")

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

from database import Base
from db_utils import init_db
from jobs.cron_setup import setup_jobs, teardown_jobs
from routers import decisions, patterns, query, repos, sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./shadow_cto.db")
    init_db(database_url)

    from db_utils import get_engine
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await setup_jobs()
    yield
    await teardown_jobs()


app = FastAPI(title="Shadow CTO", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repos.router)
app.include_router(sync.router)
app.include_router(decisions.router)
app.include_router(query.router)
app.include_router(patterns.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "shadow-cto"}


@app.get("/api/jobs")
async def list_hermes_jobs():
    from hermes_session import get_hermes_client
    hermes = get_hermes_client()
    return await hermes.list_jobs()
