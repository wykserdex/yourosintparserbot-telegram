"""Privacy Ports: Blind Index, KeyStore, and Masking."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class BlindIndexValue:
    """Versioned HMAC blind index representation."""

    version: str
    digest: str

    @property
    def value(self) -> str:
        return f"{self.version}:{self.digest}"


class BlindIndexPort(Protocol):
    """Port for computing deterministic zero-knowledge blind indexes."""

    def make_blind_index(self, normalized_value: str) -> BlindIndexValue: ...

    def normalize_email(self, email: str) -> str: ...

    def normalize_phone(self, phone: str) -> str: ...

    def rotate_blind_index(
        self,
        normalized_value: str,
        old_key: bytes,
        new_key: bytes,
        old_version: str,
        new_version: str,
    ) -> tuple[BlindIndexValue, BlindIndexValue]: ...


class MaskingPort(Protocol):
    """Port for masking sensitive values."""

    def mask_value(self, value: str, entity_type: str) -> str: ...


class KeyStorePort(Protocol):
    """Port for retrieving and rotating HMAC signing keys."""

    def get_current_key(self) -> tuple[str, bytes]: ...

    def get_key_by_version(self, version: str) -> bytes | None: ...
