"""FastAPI shared dependencies."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from yourosint.bootstrap import Container, container


def get_container() -> Container:
    """Dependency returning the global DI container."""
    return container


async def get_db_session(
    c: Container = Depends(get_container),
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding a transactional database session."""
    async with c.db.session() as session:
        yield session
