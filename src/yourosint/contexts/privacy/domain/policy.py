"""Privacy Domain: Retention policy definitions."""

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class DataRetentionPolicy:
    """Configurable data retention and pruning policy."""

    raw_message_retention: timedelta = timedelta(days=90)
    evidence_retention: timedelta = timedelta(days=365)
    audit_log_retention: timedelta = timedelta(days=730)
    anonymize_after_retention: bool = True
