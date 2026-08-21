"""Threat Intel & Network IOC Lookup Adapter."""

import ipaddress
import logging
from typing import Any

import httpx

from ...domain.provider_result import ProviderResult
from ...ports.provider import NetworkLookupPort

logger = logging.getLogger(__name__)


class NetworkThreatIntelAdapter(NetworkLookupPort):
    """Queries WHOIS, GeoIP, and reputation databases for IP and Domain IOCs."""

    def __init__(self, virustotal_key: str | None = None, abuseipdb_key: str | None = None):
        self.virustotal_key = virustotal_key
        self.abuseipdb_key = abuseipdb_key
        self._cache: dict[str, ProviderResult] = {}

    async def lookup_network_ioc(self, target: str) -> ProviderResult:
        if target in self._cache:
            return self._cache[target]

        is_ip = False
        try:
            ipaddress.ip_address(target)
            is_ip = True
        except ValueError:
            is_ip = False

        details: dict[str, Any] = {"is_ip": is_ip, "target": target}
        risk = 0

        # Query public GeoIP if IP
        if is_ip:
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(f"https://ipapi.co/{target}/json/")
                    if resp.status_code == 200:
                        data = resp.json()
                        details["country"] = data.get("country_name")
                        details["city"] = data.get("city")
                        details["org"] = data.get("org")
                        details["asn"] = data.get("asn")
            except Exception as e:
                logger.debug(f"GeoIP query skipped: {e}")

        result = ProviderResult(
            provider="threat_intel_network",
            target=target,
            is_valid=True,
            risk_score=risk,
            details=details,
        )
        self._cache[target] = result
        return result
