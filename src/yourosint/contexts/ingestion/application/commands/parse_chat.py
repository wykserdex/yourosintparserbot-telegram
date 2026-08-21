"""Command & Handler: Parse Telegram Chat."""

import logging
import time
from dataclasses import dataclass

from .....shared.application.command import Command, CommandHandler
from .....shared.domain.events import EventBus, MessageImported
from .....shared.domain.exceptions import AccountPoolExhaustedError
from ...adapters.telegram.parser import SmartParser
from ...domain.chat import Chat
from ...domain.message import RawMessage
from ...ports.repositories import ChatRepositoryPort, MessageRepositoryPort
from ...ports.telegram import AccountPoolPort
from ..dto import ParseChatResultDTO

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ParseChatCommand(Command):
    chat_username: str
    limit: int = 500
    enable_pii_filter: bool = True


class ParseChatHandler(CommandHandler[ParseChatResultDTO]):
    """Orchestrates Telegram stream parsing, persistence, and domain event publishing."""

    def __init__(
        self,
        account_pool: AccountPoolPort,
        message_repo: MessageRepositoryPort,
        chat_repo: ChatRepositoryPort,
        event_bus: EventBus | None = None,
    ):
        self.account_pool = account_pool
        self.message_repo = message_repo
        self.chat_repo = chat_repo
        self.event_bus = event_bus

    async def handle(self, cmd: ParseChatCommand) -> ParseChatResultDTO:
        start_time = time.time()
        clean_chat = cmd.chat_username.lstrip("@").strip().lower()
        logger.info(f"Executing ParseChatCommand for @{clean_chat} (limit: {cmd.limit})")

        # 1. Acquire client from AccountPool
        client = await self.account_pool.get_next_available(chat_username=clean_chat)
        if not client:
            raise AccountPoolExhaustedError("No active Telegram account available in pool")

        parser = SmartParser(client=client)

        # 2. Check monitored chat cursor
        monitored = await self.chat_repo.get_chat(clean_chat)
        min_id = monitored.last_parsed_id if monitored else 0

        messages_batch: list[RawMessage] = []
        max_seen_id = min_id

        try:
            async for msg in parser.parse_chat(chat=clean_chat, limit=cmd.limit, min_id=min_id):
                messages_batch.append(msg)
                if msg.message_id > max_seen_id:
                    max_seen_id = msg.message_id

                # Publish domain event for downstream contexts (e.g. intelligence extraction)
                if self.event_bus and msg.text:
                    await self.event_bus.publish(
                        MessageImported(
                            event_id=f"msg_{msg.chat_id}_{msg.message_id}",
                            message_id=msg.message_id,
                            chat_username=clean_chat,
                            chat_id=msg.chat_id,
                            text_content=msg.text,
                            sender_username=msg.sender_username,
                        )
                    )

                if len(messages_batch) >= 100:
                    await self.message_repo.bulk_save_messages(messages_batch)
                    messages_batch.clear()

            if messages_batch:
                await self.message_repo.bulk_save_messages(messages_batch)

            # Update chat tracking
            added_count = len(messages_batch)
            if monitored:
                await self.chat_repo.update_cursor(clean_chat, max_seen_id, added_count)
            else:
                await self.chat_repo.add_chat(
                    Chat(
                        id=None,
                        username=clean_chat,
                        last_parsed_id=max_seen_id,
                        total_messages=added_count,
                        is_active=True,
                    )
                )

        except Exception as e:
            logger.error(f"Error parsing chat @{clean_chat}: {e}")
            await self.account_pool.report_error(client)
            raise

        duration = time.time() - start_time
        return ParseChatResultDTO(
            chat_username=clean_chat,
            messages_parsed=len(messages_batch),
            messages_saved=len(messages_batch),
            duration_seconds=round(duration, 2),
        )
