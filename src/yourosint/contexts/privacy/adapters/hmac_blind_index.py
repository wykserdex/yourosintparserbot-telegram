"""HMAC-SHA256 Blind Index and Masking Service Adapter."""

import hashlib
import hmac
import unicodedata

from ..ports.blind_index import BlindIndexPort, BlindIndexValue, MaskingPort


class HMACBlindIndexService(BlindIndexPort, MaskingPort):
    """Provides cryptographic blind indexing with versioned rotation and safe masking."""

    def __init__(self, key: str | bytes, version: str = "v1"):
        self.key = key.encode("utf-8") if isinstance(key, str) else key
        self.version = version

    def normalize_email(self, value: str) -> str:
        return unicodedata.normalize("NFKC", value).strip().casefold()

    def normalize_phone(self, value: str) -> str:
        digits = "".join(c for c in value if c.isdigit())
        if digits.startswith("8") and len(digits) == 11:
            digits = "7" + digits[1:]
        return digits

    def make_blind_index(
        self,
        normalized_value: str,
        *,
        key: bytes | None = None,
        key_version: str | None = None,
    ) -> BlindIndexValue:
        active_key = key or self.key
        active_version = key_version or self.version

        digest = hmac.new(
            active_key,
            normalized_value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return BlindIndexValue(version=active_version, digest=digest)

    def rotate_blind_index(
        self,
        normalized_value: str,
        old_key: bytes,
        new_key: bytes,
        old_version: str,
        new_version: str,
    ) -> tuple[BlindIndexValue, BlindIndexValue]:
        old_idx = self.make_blind_index(normalized_value, key=old_key, key_version=old_version)
        new_idx = self.make_blind_index(normalized_value, key=new_key, key_version=new_version)
        return old_idx, new_idx

    def mask_value(self, value: str, entity_type: str) -> str:
        if not value:
            return ""

        e_type = str(entity_type).lower()

        if e_type in ["card", "bank_card"]:
            digits = "".join(c for c in value if c.isdigit())
            if len(digits) >= 4:
                return f"**** **** **** {digits[-4:]}"
            return "****"

        if e_type == "phone":
            digits = "".join(c for c in value if c.isdigit())
            if len(digits) >= 7:
                return f"+{digits[:2]} *** *** {digits[-4:]}"
            if len(digits) >= 4:
                return f"***{digits[-4:]}"
            return "****"

        if e_type == "email":
            parts = value.split("@")
            if len(parts) == 2:
                name, domain = parts
                masked_name = name[0] + "***" if len(name) > 1 else "*"
                return f"{masked_name}@{domain}"
            return "***@***"

        return value
