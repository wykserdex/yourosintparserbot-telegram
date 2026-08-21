"""Application Command primitives for CQRS."""

from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

R_co = TypeVar("R_co", covariant=True)


@dataclass(frozen=True, slots=True)
class Command:
    """Base marker for write operations."""


class CommandHandler(Protocol[R_co]):
    """Handler executing a state-modifying command."""

    async def handle(self, command: Any) -> R_co: ...
