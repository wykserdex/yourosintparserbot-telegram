"""Enrichment Domain: Provider Result value object."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderResult:
    """Standardized response from external intelligence provider."""

    provider: str
    target: str
    is_valid: bool
    risk_score: int = 0
    details: dict[str, Any] = field(default_factory=dict)
