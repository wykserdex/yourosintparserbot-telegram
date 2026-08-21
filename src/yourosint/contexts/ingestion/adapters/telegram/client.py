"""Smart Telegram Client Adapter."""

import asyncio
import logging
import random
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ...domain.message import RawMessage

logger = logging.getLogger(__name__)


class SmartTelegramClient:
    """Telethon client wrapper with anti-detection spoofing and exponential retry."""

    def __init__(
        self,
        session_name: str,
        api_id: int = 0,
        api_hash: str = "",
        phone: str | None = None,
        proxy: dict[str, Any] | None = None,
        pool: Any | None = None,
    ):
        self.session_name = session_name
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.proxy = proxy
        self.pool = pool
        self.client: Any | None = None
        self._created_at = time.time()
        self.stats = {"requests": 0, "floods": 0, "errors": 0}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type(Exception),
    )
    async def start(self) -> None:
        if not self.api_id or not self.api_hash:
            logger.debug(f"SmartTelegramClient {self.session_name} starting in test/mock mode")
            return

        try:
            from telethon import TelegramClient
            from telethon.network.connection.tcpfull import ConnectionTcpFull

            device_models = [
                "Telegram Desktop",
                "Telegram Android",
                "Telegram iOS",
                "Telegram macOS",
            ]
            app_versions = ["4.16.30", "5.1.0", "5.2.2"]

            self.client = TelegramClient(
                f"sessions/{self.session_name}",
                self.api_id,
                self.api_hash,
                connection=ConnectionTcpFull,
                proxy=self.proxy,
                device_model=random.choice(device_models),
                system_version="Linux x86_64",
                app_version=random.choice(app_versions),
            )
            await self.client.start(phone=self.phone)
            logger.info(f"Connected Telegram client: {self.session_name}")
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to start client {self.session_name}: {e}")
            raise

    async def stop(self) -> None:
        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                logger.debug(f"Disconnect error on {self.session_name}: {e}")
            finally:
                self.client = None

    async def get_me(self) -> dict[str, Any] | None:
        if not self.client:
            return {"username": f"{self.session_name}_mock", "phone": self.phone or "mock"}
        try:
            me = await self.client.get_me()
            if me:
                return {
                    "id": me.id,
                    "username": getattr(me, "username", None),
                    "phone": getattr(me, "phone", None),
                    "first_name": getattr(me, "first_name", None),
                }
        except Exception as e:
            logger.warning(f"get_me failed on {self.session_name}: {e}")
            if self.pool:
                await self.pool.report_error(self)
        return None

    async def iter_messages(
        self, chat: str | int, limit: int = 100, min_id: int = 0
    ) -> AsyncIterator[RawMessage]:
        """Streams messages from a Telegram chat."""
        self.stats["requests"] += 1
        if not self.client:
            # Yield mock sample message for unit testing / dry runs
            yield RawMessage(
                message_id=random.randint(1000, 99999),
                chat_id=123456789,
                chat_username=str(chat).lstrip("@"),
                sender_id=987654321,
                sender_username="target_user",
                sender_first_name="Target",
                sender_last_name="Investigated",
                text=f"Sample parsed message from {chat} with contact@target.com and +79991234567",
                posted_at=datetime.now(UTC),
            )
            return

        try:
            async for raw_msg in self.client.iter_messages(chat, limit=limit, min_id=min_id):
                sender = await raw_msg.get_sender()
                chat_entity = await raw_msg.get_chat()

                chat_username = getattr(chat_entity, "username", None)
                chat_title = getattr(chat_entity, "title", None)

                sender_id = getattr(sender, "id", None)
                sender_username = getattr(sender, "username", None)
                sender_first = getattr(sender, "first_name", None)
                sender_last = getattr(sender, "last_name", None)

                yield RawMessage(
                    message_id=raw_msg.id,
                    chat_id=raw_msg.chat_id,
                    chat_title=chat_title,
                    chat_username=chat_username,
                    sender_id=sender_id,
                    sender_username=sender_username,
                    sender_first_name=sender_first,
                    sender_last_name=sender_last,
                    text=raw_msg.text or "",
                    posted_at=raw_msg.date or datetime.now(UTC),
                    has_media=bool(raw_msg.media),
                    media_type=type(raw_msg.media).__name__ if raw_msg.media else None,
                )
        except Exception as e:
            self.stats["errors"] += 1
            if "FloodWait" in str(type(e)):
                wait_sec = getattr(e, "seconds", 60)
                logger.warning(f"FloodWait on {self.session_name}: {wait_sec}s")
                if self.pool:
                    await self.pool.report_flood(self, wait_sec)
            raise

    async def search_global(self, query: str, limit: int = 100) -> list[str]:
        if not self.client:
            return [f"search_{query}_channel", f"{query}_community"]

        found: list[str] = []
        try:
            from telethon import helpers

            async for msg in self.client.iter_messages(None, search=query, limit=limit):
                chat = msg.chat
                if not hasattr(chat, "username") or not chat.username:
                    continue
                try:
                    entity_type = helpers._entity_type(chat)
                    if entity_type in [helpers._EntityType.CHANNEL, helpers._EntityType.CHAT]:
                        u = chat.username.lstrip("@").strip().lower()
                        if u not in found:
                            found.append(u)
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Global search error: {e}")
        return found

    async def query_bot(
        self, bot_username: str, query: str, wait_seconds: float = 4.0
    ) -> list[str]:
        if not self.client:
            return [f"discovered_from_{query}_chat1", f"discovered_from_{query}_chat2"]

        import re

        clean_bot = f"@{bot_username.lstrip('@')}"
        found: list[str] = []
        try:
            await self.client.send_message(clean_bot, query)
            await asyncio.sleep(wait_seconds)

            async for msg in self.client.iter_messages(clean_bot, limit=10):
                if msg.text and ("@" in msg.text or "t.me/" in msg.text):
                    usernames = re.findall(r"@([a-zA-Z0-9_]{4,32})", msg.text)
                    tme_links = re.findall(r"t\.me/([a-zA-Z0-9_]{4,32})", msg.text)
                    for u in usernames + tme_links:
                        clean_u = u.strip().lower()
                        if clean_u != bot_username.lstrip("@").lower() and clean_u not in found:
                            found.append(clean_u)
        except Exception as e:
            logger.warning(f"Bot query error ({bot_username}): {e}")
        return found
