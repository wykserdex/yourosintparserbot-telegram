"""Database session and connection pool management."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from ...config.settings import Settings, get_settings
from ...contexts.ingestion.adapters.persistence.models import IngestionBase
from ...contexts.intelligence.adapters.persistence.models import IntelligenceBase

logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    """Manages AsyncEngine, AsyncSession, and SQLite fallback."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self.init_engine()
        assert self._engine is not None
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self.init_engine()
        assert self._session_factory is not None
        return self._session_factory

    def init_engine(self, url: str | None = None) -> None:
        db_url = url or self.settings.DATABASE_URL
        is_sqlite = db_url.startswith("sqlite")

        if is_sqlite:
            self._engine = create_async_engine(
                db_url,
                poolclass=NullPool,
                echo=self.settings.DEBUG,
            )
        else:
            self._engine = create_async_engine(
                db_url,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_pre_ping=True,
                echo=self.settings.DEBUG,
            )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info(
            f"Database session manager initialized for {db_url.split('@')[-1] if '@' in db_url else db_url}"
        )

    async def create_all_tables(self) -> None:
        """Create all tables across bounded contexts."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(IngestionBase.metadata.create_all)
                await conn.run_sync(IntelligenceBase.metadata.create_all)
        except Exception as e:
            if self.settings.SQLITE_FALLBACK and not self.settings.DATABASE_URL.startswith(
                "sqlite"
            ):
                logger.warning(
                    f"PostgreSQL connection failed ({e}), falling back to SQLite yourosint.db"
                )
                self.init_engine("sqlite+aiosqlite:///yourosint.db")
                async with self.engine.begin() as conn:
                    await conn.run_sync(IngestionBase.metadata.create_all)
                    await conn.run_sync(IntelligenceBase.metadata.create_all)
            else:
                raise

    async def drop_all_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(IntelligenceBase.metadata.drop_all)
            await conn.run_sync(IngestionBase.metadata.drop_all)

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise
