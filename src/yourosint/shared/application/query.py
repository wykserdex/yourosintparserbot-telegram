"""Application Query primitives for CQRS."""

from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

T_co = TypeVar("T_co", covariant=True)


@dataclass(frozen=True, slots=True)
class Query:
    """Base marker for read-only operations."""


class QueryHandler(Protocol[T_co]):
    """Handler executing an analytical or lookup query."""

    async def handle(self, query: Any) -> T_co: ...
