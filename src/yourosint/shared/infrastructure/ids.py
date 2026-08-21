"""Unique and deterministic identifier generators."""

import hashlib
import uuid


def generate_uuid() -> str:
    """Generates standard UUIDv4 string."""
    return str(uuid.uuid4())


def deterministic_id(prefix: str, *components: str) -> str:
    """Generates deterministic SHA-256 fingerprint for deduplication."""
    payload = ":".join(str(c).strip().lower() for c in components)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
