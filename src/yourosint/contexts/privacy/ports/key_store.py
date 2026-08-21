"""Privacy Ports: Key Store interface."""

from typing import Protocol


class KeyStorePort(Protocol):
    """Abstract interface for managing cryptographic blind index keys."""

    def get_current_key(self) -> tuple[str, bytes]: ...

    def get_key_by_version(self, version: str) -> bytes | None: ...
