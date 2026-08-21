"""Privacy Domain: PII types and masking definitions."""

from dataclasses import dataclass, field
from enum import StrEnum


class PIIType(StrEnum):
    """Personal Identifiable Information categories."""

    PASSPORT = "PASSPORT"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    BANK_CARD = "BANK_CARD"
    SNILS = "SNILS"
    INN = "INN"
    BIRTH_DATE = "BIRTH_DATE"


@dataclass(frozen=True, slots=True)
class PIIMaskResult:
    """Sanitized text and detected PII entities."""

    sanitized_text: str
    detected_pii: list[str] = field(default_factory=list)
    has_pii: bool = False
