"""Command & Handler: Direct message batch import."""

from collections.abc import Sequence
from dataclasses import dataclass

from .....shared.application.command import Command, CommandHandler
from ...domain.message import RawMessage
from ...ports.repositories import MessageRepositoryPort


@dataclass(frozen=True, slots=True)
class ImportMessagesCommand(Command):
    messages: Sequence[RawMessage]


class ImportMessagesHandler(CommandHandler[int]):
    """Saves raw messages directly into repository."""

    def __init__(self, message_repo: MessageRepositoryPort):
        self.message_repo = message_repo

    async def handle(self, cmd: ImportMessagesCommand) -> int:
        return await self.message_repo.bulk_save_messages(cmd.messages)
