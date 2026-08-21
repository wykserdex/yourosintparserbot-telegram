"""Autopilot Worker Entrypoint."""

import asyncio
import contextlib
import json
import logging
import random
from datetime import UTC, datetime
from pathlib import Path

from yourosint.bootstrap import Container
from yourosint.contexts.ingestion.adapters.persistence.repositories import (
    SQLAlchemyChatRepository,
    SQLAlchemyMessageRepository,
)
from yourosint.contexts.ingestion.application.commands.parse_chat import (
    ParseChatCommand,
    ParseChatHandler,
)

logger = logging.getLogger(__name__)


class AutopilotWorker:
    """Orchestrates continuous discovery and ingestion of monitored channels."""

    def __init__(self, container: Container, state_file: Path = Path("autopilot_state.json")):
        self.container = container
        self.state_file = state_file
        self.is_running = False
        self._task: asyncio.Task | None = None
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"iteration": 0, "total_parsed": 0, "status": "stopped", "last_run": None}

    def _save_state(self) -> None:
        try:
            self.state["last_run"] = datetime.now(UTC).isoformat()
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception:
            pass

    async def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self.state["status"] = "running"
        self._save_state()
        self._task = asyncio.create_task(self._loop())
        logger.info("Autopilot worker started")

    async def stop(self) -> None:
        self.is_running = False
        self.state["status"] = "stopped"
        self._save_state()
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("Autopilot worker stopped")

    async def _loop(self) -> None:
        while self.is_running:
            try:
                self.state["iteration"] += 1
                logger.info(f"Autopilot cycle #{self.state['iteration']}")

                async with self.container.db.session() as session:
                    chat_repo = SQLAlchemyChatRepository(session)
                    msg_repo = SQLAlchemyMessageRepository(session)

                    chats = await chat_repo.list_chats(active_only=True)
                    handler = ParseChatHandler(
                        account_pool=self.container.account_pool,
                        message_repo=msg_repo,
                        chat_repo=chat_repo,
                        event_bus=self.container.event_bus,
                    )

                    for chat in chats[:5]:
                        if not self.is_running:
                            break
                        try:
                            res = await handler.handle(
                                ParseChatCommand(chat_username=chat.username, limit=100)
                            )
                            self.state["total_parsed"] += res.messages_parsed
                        except Exception as e:
                            logger.warning(f"Error parsing @{chat.username}: {e}")
                        await asyncio.sleep(random.uniform(5, 10))

                self._save_state()
                await asyncio.sleep(random.uniform(30, 60))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Autopilot error: {e}")
                await asyncio.sleep(20)
