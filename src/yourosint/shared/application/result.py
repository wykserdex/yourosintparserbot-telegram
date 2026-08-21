"""Result monad envelope for application operations."""

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


@dataclass(frozen=True, slots=True)
class Result(Generic[T, E]):
    """Encapsulates success or failure without raising exceptions across boundaries."""

    is_success: bool
    value: T | None = None
    error: E | None = None

    @classmethod
    def ok(cls, value: T) -> "Result[T, Any]":
        return cls(is_success=True, value=value, error=None)

    @classmethod
    def fail(cls, error: E) -> "Result[Any, E]":
        return cls(is_success=False, value=None, error=error)

    def unwrap(self) -> T:
        if not self.is_success:
            raise self.error or Exception("Unwrap failed on Result.fail")
        assert self.value is not None
        return self.value
