"""
Integration test fixtures.

DB:   in-memory SQLite via aiosqlite + SQLAlchemy async.
       Each test gets a fresh, rolled-back transaction — no persistent state.

MinIO: skipped unless MINIO_ENDPOINT env var is set.
"""
import os
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from xime.starters.sqlalchemy import Base


# ── SQLite engine (one per test session) ─────────────────────────────────────

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def _engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_engine) -> AsyncSession:
    """
    Yields an AsyncSession wrapped in a savepoint so each test
    is automatically rolled back without touching the schema.
    """
    async_session = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ── FakeSessionFactory — wraps AsyncSession for repository injection ──────────

class FakeSessionFactory:
    """Adapts AsyncSession to the AsyncSessionFactory interface used by repositories."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def current(self) -> AsyncSession:
        return self._session


# ── Fake transaction — no-op context manager for use-case tests ──────────────

@asynccontextmanager
async def fake_transaction():
    """
    Replaces TransactionManager in use-case tests.
    Repositories share the db_session fixture, so real session management
    is handled externally by the fixture.
    """
    yield


# ── MinIO skip guard ──────────────────────────────────────────────────────────

requires_minio = pytest.mark.skipif(
    not os.environ.get("MINIO_ENDPOINT"),
    reason="MINIO_ENDPOINT env var not set — set it to run MinIO integration tests",
)
