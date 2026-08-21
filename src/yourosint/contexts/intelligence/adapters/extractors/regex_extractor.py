"""Regex Entity Extractor Adapter."""

import ipaddress
import re
import unicodedata

from ...domain.entity import EntityType
from ...ports.extractor import EntityExtractorPort


class RegexEntityExtractor(EntityExtractorPort):
    """Production-grade regular expression entity extractor."""

    def __init__(self):
        self.patterns = {
            EntityType.EMAIL: re.compile(
                r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
                re.IGNORECASE,
            ),
            EntityType.DOMAIN: re.compile(
                r"(?:https?://)?(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}",
                re.IGNORECASE,
            ),
            EntityType.IP: re.compile(
                r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
            ),
            EntityType.PHONE: re.compile(
                r"(?:\+7|8|\+380|\+1|\+44)?[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{2,4}[\s\-]?\d{2,4}[\s\-]?\d{2,4}\b",
                re.IGNORECASE,
            ),
            EntityType.CARD: re.compile(
                r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13})\b"
            ),
            EntityType.CRYPTO_BTC: re.compile(
                r"\b(?:[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{25,39})\b"
            ),
            EntityType.CRYPTO_ETH: re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
            EntityType.USERNAME: re.compile(
                r"(?<![\w@])@([a-zA-Z0-9_]{4,32})\b",
                re.IGNORECASE,
            ),
        }

    def extract_all(self, text: str) -> dict[EntityType, list[str]]:
        if not text:
            return {}

        extracted: dict[EntityType, list[str]] = {}
        for entity_type, pattern in self.patterns.items():
            matches = [m.group(0) for m in pattern.finditer(text)]
            if matches:
                cleaned = self._clean_matches(matches, entity_type)
                if cleaned:
                    extracted[entity_type] = list(set(cleaned))

        return extracted

    def _clean_matches(self, matches: list[str], entity_type: EntityType) -> list[str]:
        cleaned: list[str] = []
        for match in matches:
            val = str(match).strip()
            if not val or len(val) < 2:
                continue

            if entity_type == EntityType.EMAIL:
                norm_email = unicodedata.normalize("NFKC", val).strip().casefold()
                if "@" in norm_email and "." in norm_email.split("@")[-1]:
                    cleaned.append(norm_email)
            elif entity_type == EntityType.DOMAIN:
                dom = (
                    val.replace("http://", "")
                    .replace("https://", "")
                    .replace("www.", "")
                    .strip("/")
                    .lower()
                )
                if (
                    "." in dom
                    and len(dom) >= 4
                    and not any(d in dom for d in ["t.me", "telegram.me", "localhost"])
                ):
                    cleaned.append(dom)
            elif entity_type == EntityType.IP:
                try:
                    ip = ipaddress.ip_address(val)
                    if not (ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_multicast):
                        cleaned.append(str(ip))
                except ValueError:
                    pass
            elif entity_type == EntityType.PHONE:
                digits = "".join(c for c in val if c.isdigit())
                if digits.startswith("8") and len(digits) == 11:
                    digits = "7" + digits[1:]
                if 10 <= len(digits) <= 15:
                    cleaned.append(digits)
            elif entity_type == EntityType.CARD:
                digits = "".join(c for c in val if c.isdigit())
                if len(digits) in [15, 16] and self._luhn_check(digits):
                    cleaned.append(digits)
            elif entity_type == EntityType.USERNAME:
                u = val.lstrip("@").strip().lower()
                if 4 <= len(u) <= 32 and u not in [
                    "everyone",
                    "here",
                    "channel",
                    "admin",
                    "null",
                    "none",
                ]:
                    cleaned.append(u)
            elif entity_type in [EntityType.CRYPTO_BTC, EntityType.CRYPTO_ETH]:
                cleaned.append(val)

        return cleaned

    def _luhn_check(self, card_number: str) -> bool:
        digits = [int(c) for c in card_number if c.isdigit()]
        if not digits:
            return False
        checksum = 0
        reverse_digits = digits[::-1]
        for i, digit in enumerate(reverse_digits):
            if i % 2 == 1:
                doubled = digit * 2
                checksum += doubled - 9 if doubled > 9 else doubled
            else:
                checksum += digit
        return checksum % 10 == 0
