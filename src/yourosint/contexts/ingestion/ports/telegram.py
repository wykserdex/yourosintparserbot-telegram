"""Ingestion Ports: Telegram Client and Account Pool interfaces."""

from collections.abc import AsyncIterator
from typing import Any, Protocol

from ..domain.message import RawMessage


class TelegramPort(Protocol):
    """Abstract interface for communicating with Telegram API."""

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def get_me(self) -> dict[str, Any] | None: ...

    async def iter_messages(
        self, chat: str | int, limit: int = 100, min_id: int = 0
    ) -> AsyncIterator[RawMessage]: ...

    async def search_global(self, query: str, limit: int = 100) -> list[str]: ...

    async def query_bot(
        self, bot_username: str, query: str, wait_seconds: float = 4.0
    ) -> list[str]: ...


class AccountPoolPort(Protocol):
    """Abstract interface for managing rotating pool of Telegram accounts."""

    async def initialize(self, account_names: list[str] | None = None) -> list[dict[str, Any]]: ...

    async def get_next_available(
        self, chat_username: str | None = None, prefer_same: bool = True
    ) -> TelegramPort | None: ...

    async def report_flood(self, client: TelegramPort, wait_seconds: int) -> None: ...

    async def report_error(self, client: TelegramPort) -> None: ...

    async def rotate_session(self, session_name: str) -> None: ...

    async def get_stats(self) -> dict[str, Any]: ...

    async def close_all(self) -> None: ...
