"""Global Test Fixtures."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from yourosint.config.settings import Settings
from yourosint.contexts.ingestion.adapters.persistence.models import IngestionBase
from yourosint.contexts.intelligence.adapters.persistence.models import IntelligenceBase


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        BLIND_INDEX_KEY="test-secret-hmac-key-v1",
        BLIND_INDEX_KEY_VERSION="v1",
        DEBUG=False,
    )


@pytest_asyncio.fixture
async def async_engine(test_settings: Settings):
    engine = create_async_engine(test_settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(IngestionBase.metadata.create_all)
        await conn.run_sync(IntelligenceBase.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(IntelligenceBase.metadata.drop_all)
        await conn.run_sync(IngestionBase.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
