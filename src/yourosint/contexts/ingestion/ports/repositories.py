"""Ingestion Ports: Persistence repositories."""

from collections.abc import Sequence
from typing import Protocol

from ..domain.chat import Chat
from ..domain.message import RawMessage


class MessageRepositoryPort(Protocol):
    """Repository port for raw Telegram messages."""

    async def save_message(self, message: RawMessage) -> RawMessage: ...

    async def bulk_save_messages(self, messages: Sequence[RawMessage]) -> int: ...

    async def search_messages(
        self,
        query: str,
        chat_username: str | None = None,
        sender_username: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RawMessage], int]: ...

    async def get_total_stats(self) -> dict[str, int]: ...


class ChatRepositoryPort(Protocol):
    """Repository port for monitored channels."""

    async def add_chat(self, chat: Chat) -> Chat: ...

    async def get_chat(self, username: str) -> Chat | None: ...

    async def list_chats(self, active_only: bool = True) -> list[Chat]: ...

    async def update_cursor(self, username: str, last_parsed_id: int, new_count: int) -> None: ...
