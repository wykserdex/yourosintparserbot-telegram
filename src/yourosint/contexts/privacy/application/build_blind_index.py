"""Command & Handler: Generate Blind Index."""

from dataclasses import dataclass

from ....shared.application.command import Command, CommandHandler
from ..ports.blind_index import BlindIndexPort, BlindIndexValue


@dataclass(frozen=True, slots=True)
class BuildBlindIndexCommand(Command):
    value: str
    entity_type: str


class BuildBlindIndexHandler(CommandHandler[BlindIndexValue]):
    def __init__(self, blind_index_port: BlindIndexPort):
        self.blind_index_port = blind_index_port

    async def handle(self, cmd: BuildBlindIndexCommand) -> BlindIndexValue:
        e_type = cmd.entity_type.lower()
        if e_type == "email":
            norm = self.blind_index_port.normalize_email(cmd.value)
        elif e_type == "phone":
            norm = self.blind_index_port.normalize_phone(cmd.value)
        else:
            norm = cmd.value.strip().casefold()

        return self.blind_index_port.make_blind_index(norm)
