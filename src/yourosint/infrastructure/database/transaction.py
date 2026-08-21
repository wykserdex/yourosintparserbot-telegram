"""Unit of Work transaction management."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork(Protocol):
    """Abstract Unit of Work interface."""

    session: AsyncSession

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class SqlAlchemyUnitOfWork:
    """Async SQLAlchemy Unit of Work implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
