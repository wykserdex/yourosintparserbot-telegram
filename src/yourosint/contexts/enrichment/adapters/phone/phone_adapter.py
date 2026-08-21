"""Phone Lookup Adapter using libphonenumber."""

import logging
import re
from typing import Any

from ...ports.provider import PhoneLookupPort

logger = logging.getLogger(__name__)


class LibphonenumberAdapter(PhoneLookupPort):
    """Parses, normalizes, and extracts carrier/geo details for international phone numbers."""

    def lookup_phone(self, phone: str) -> dict[str, Any]:
        clean = re.sub(r"[^\d+]", "", phone)
        if clean.startswith("8") and len(clean) == 11:
            clean = "+7" + clean[1:]
        elif not clean.startswith("+"):
            clean = "+" + clean

        try:
            import phonenumbers
            from phonenumbers import carrier, geocoder, timezone

            parsed = phonenumbers.parse(clean, None)
            is_valid = phonenumbers.is_valid_number(parsed)

            return {
                "raw": phone,
                "clean": clean,
                "valid": is_valid,
                "international": phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                ),
                "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
                "country": geocoder.description_for_number(parsed, "en") if is_valid else None,
                "carrier": carrier.name_for_number(parsed, "en") if is_valid else None,
                "timezones": list(timezone.time_zones_for_number(parsed)) if is_valid else [],
                "messengers": {
                    "telegram": f"https://t.me/{clean.lstrip('+')}",
                    "whatsapp": f"https://wa.me/{clean.lstrip('+')}",
                    "viber": f"viber://add?number={clean.lstrip('+')}",
                },
            }
        except Exception as e:
            logger.debug(f"Libphonenumber parse error on {phone}: {e}")
            digits = "".join(c for c in phone if c.isdigit())
            return {
                "raw": phone,
                "clean": digits,
                "valid": len(digits) >= 10,
                "international": f"+{digits}",
                "messengers": {"telegram": f"https://t.me/{digits}"},
            }
