"""Shared domain entity base classes."""

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

EntityId = TypeVar("EntityId")


@dataclass(slots=True)
class Entity(Generic[EntityId]):
    """Base domain entity with identity-based equality."""

    id: EntityId

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((self.__class__, self.id))
