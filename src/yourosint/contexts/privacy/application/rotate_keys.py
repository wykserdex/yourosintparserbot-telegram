"""Command & Handler: Rotate Blind Index Keys."""

from dataclasses import dataclass

from ....shared.application.command import Command, CommandHandler
from ..ports.blind_index import BlindIndexPort, BlindIndexValue
from ..ports.key_store import KeyStorePort


@dataclass(frozen=True, slots=True)
class RotateKeysCommand(Command):
    new_version: str
    new_key: bytes


class RotateKeysHandler(CommandHandler[tuple[BlindIndexValue, BlindIndexValue]]):
    def __init__(self, blind_index_port: BlindIndexPort, key_store: KeyStorePort):
        self.blind_index_port = blind_index_port
        self.key_store = key_store

    async def handle_rotation(
        self, normalized_value: str, new_version: str, new_key: bytes
    ) -> tuple[BlindIndexValue, BlindIndexValue]:
        old_version, old_key = self.key_store.get_current_key()
        return self.blind_index_port.rotate_blind_index(
            normalized_value=normalized_value,
            old_key=old_key,
            new_key=new_key,
            old_version=old_version,
            new_version=new_version,
        )
