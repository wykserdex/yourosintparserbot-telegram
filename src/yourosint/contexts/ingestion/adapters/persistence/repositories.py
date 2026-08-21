"""SQLAlchemy 2.0 Async Repositories for Ingestion context."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.chat import Chat
from ...domain.message import RawMessage
from ...ports.repositories import ChatRepositoryPort, MessageRepositoryPort
from .models import MessageORM, MonitoredChatORM


class SQLAlchemyMessageRepository(MessageRepositoryPort):
    """SQLAlchemy async repository for RawMessages."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_message(self, message: RawMessage) -> RawMessage:
        stmt = select(MessageORM).where(
            MessageORM.chat_id == message.chat_id,
            MessageORM.message_id == message.message_id,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.message_text = message.text
            existing.sender_username = message.sender_username
            existing.sender_first_name = message.sender_first_name
            existing.sender_last_name = message.sender_last_name
            await self.session.flush()
            return self._orm_to_domain(existing)

        orm = MessageORM(
            message_id=message.message_id,
            chat_id=message.chat_id,
            chat_title=message.chat_title,
            chat_username=message.chat_username.lstrip("@") if message.chat_username else None,
            sender_id=message.sender_id,
            sender_username=message.sender_username.lstrip("@")
            if message.sender_username
            else None,
            sender_first_name=message.sender_first_name,
            sender_last_name=message.sender_last_name,
            message_text=message.text,
            date=message.posted_at,
            has_media=message.has_media,
            media_type=message.media_type,
            is_pii_filtered=message.is_pii_filtered,
        )
        self.session.add(orm)
        await self.session.flush()
        return self._orm_to_domain(orm)

    async def bulk_save_messages(self, messages: Sequence[RawMessage]) -> int:
        count = 0
        for m in messages:
            try:
                await self.save_message(m)
                count += 1
            except Exception:
                pass
        return count

    async def search_messages(
        self,
        query: str,
        chat_username: str | None = None,
        sender_username: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RawMessage], int]:
        stmt = select(MessageORM)
        count_stmt = select(func.count(MessageORM.id))

        filters: list[Any] = []
        if query:
            filters.append(MessageORM.message_text.ilike(f"%{query}%"))
        if chat_username:
            filters.append(MessageORM.chat_username == chat_username.lstrip("@"))
        if sender_username:
            filters.append(MessageORM.sender_username == sender_username.lstrip("@"))

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one() or 0

        stmt = stmt.order_by(MessageORM.date.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        orms = result.scalars().all()

        return [self._orm_to_domain(o) for o in orms], total

    async def get_total_stats(self) -> dict[str, int]:
        msg_count = await self.session.execute(select(func.count(MessageORM.id)))
        users_count = await self.session.execute(
            select(func.count(func.distinct(MessageORM.sender_id)))
        )
        chats_count = await self.session.execute(
            select(func.count(func.distinct(MessageORM.chat_id)))
        )

        return {
            "total_messages": msg_count.scalar_one() or 0,
            "total_users": users_count.scalar_one() or 0,
            "total_chats": chats_count.scalar_one() or 0,
        }

    def _orm_to_domain(self, orm: MessageORM) -> RawMessage:
        return RawMessage(
            id=orm.id,
            message_id=orm.message_id,
            chat_id=orm.chat_id,
            chat_title=orm.chat_title,
            chat_username=orm.chat_username,
            sender_id=orm.sender_id,
            sender_username=orm.sender_username,
            sender_first_name=orm.sender_first_name,
            sender_last_name=orm.sender_last_name,
            text=orm.message_text or "",
            posted_at=orm.date,
            has_media=orm.has_media,
            media_type=orm.media_type,
            is_pii_filtered=orm.is_pii_filtered,
        )


class SQLAlchemyChatRepository(ChatRepositoryPort):
    """SQLAlchemy async repository for Monitored Chats."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_chat(self, chat: Chat) -> Chat:
        clean = chat.clean_username
        stmt = select(MonitoredChatORM).where(MonitoredChatORM.username == clean)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.is_active = chat.is_active
            if chat.title:
                existing.title = chat.title
            if chat.chat_id:
                existing.chat_id = chat.chat_id
            await self.session.flush()
            return self._orm_to_domain(existing)

        orm = MonitoredChatORM(
            username=clean,
            title=chat.title,
            chat_id=chat.chat_id,
            last_parsed_id=chat.last_parsed_id,
            total_messages=chat.total_messages,
            is_active=chat.is_active,
            discovered_via=chat.discovered_via,
        )
        self.session.add(orm)
        await self.session.flush()
        return self._orm_to_domain(orm)

    async def get_chat(self, username: str) -> Chat | None:
        clean = username.lstrip("@").strip().lower()
        stmt = select(MonitoredChatORM).where(MonitoredChatORM.username == clean)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._orm_to_domain(orm) if orm else None

    async def list_chats(self, active_only: bool = True) -> list[Chat]:
        stmt = select(MonitoredChatORM)
        if active_only:
            stmt = stmt.where(MonitoredChatORM.is_active.is_(True))
        result = await self.session.execute(stmt)
        orms = result.scalars().all()
        return [self._orm_to_domain(o) for o in orms]

    async def update_cursor(self, username: str, last_parsed_id: int, new_count: int) -> None:
        clean = username.lstrip("@").strip().lower()
        stmt = select(MonitoredChatORM).where(MonitoredChatORM.username == clean)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm:
            orm.last_parsed_id = max(orm.last_parsed_id, last_parsed_id)
            orm.total_messages += new_count
            orm.updated_at = datetime.now(UTC)
            await self.session.flush()

    def _orm_to_domain(self, orm: MonitoredChatORM) -> Chat:
        return Chat(
            id=orm.id,
            username=orm.username,
            title=orm.title,
            chat_id=orm.chat_id,
            last_parsed_id=orm.last_parsed_id,
            total_messages=orm.total_messages,
            is_active=orm.is_active,
            discovered_via=orm.discovered_via,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
