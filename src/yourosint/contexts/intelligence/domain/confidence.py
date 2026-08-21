"""Intelligence Domain: Confidence value object."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Confidence:
    """Bounded confidence score between 0.0 and 1.0 (pure Decimal)."""

    value: Decimal

    def __post_init__(self) -> None:
        if not (Decimal("0.0") <= self.value <= Decimal("1.0")):
            raise ValueError(f"Confidence value must be between 0.0 and 1.0, got {self.value}")

    @classmethod
    def from_float(cls, val: float) -> "Confidence":
        return cls(Decimal(str(round(val, 4))))

    @property
    def is_high(self) -> bool:
        return self.value >= Decimal("0.7")

    @property
    def requires_review(self) -> bool:
        return Decimal("0.4") <= self.value < Decimal("0.7")
