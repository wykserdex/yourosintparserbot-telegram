"""Environment-backed KeyStore Adapter."""

from ...ports.key_store import KeyStorePort


class EnvKeyStore(KeyStorePort):
    """Retrieves HMAC blind index signing keys from environment config."""

    def __init__(self, key: str | bytes, version: str = "v1"):
        self._key = key.encode("utf-8") if isinstance(key, str) else key
        self._version = version
        self._key_history: dict[str, bytes] = {version: self._key}

    def get_current_key(self) -> tuple[str, bytes]:
        return self._version, self._key

    def get_key_by_version(self, version: str) -> bytes | None:
        return self._key_history.get(version)

    def register_key(self, version: str, key: str | bytes) -> None:
        key_bytes = key.encode("utf-8") if isinstance(key, str) else key
        self._key_history[version] = key_bytes
        self._version = version
        self._key = key_bytes
