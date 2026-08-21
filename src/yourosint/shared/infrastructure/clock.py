"""System clock primitives."""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Abstract clock for deterministic time in tests."""

    def now(self) -> datetime: ...


class SystemClock:
    """Production clock returning timezone-aware UTC datetime."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    """Test clock returning fixed timestamp."""

    def __init__(self, frozen_time: datetime):
        self._time = frozen_time

    def now(self) -> datetime:
        return self._time
