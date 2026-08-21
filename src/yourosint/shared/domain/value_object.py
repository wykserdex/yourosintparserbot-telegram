"""Shared value object base classes."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValueObject:
    """Base immutable value object with structural equality."""
