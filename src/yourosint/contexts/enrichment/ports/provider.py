"""Enrichment Ports: Provider interfaces."""

from typing import Any, Protocol

from ..domain.provider_result import ProviderResult


class PhoneLookupPort(Protocol):
    """Port for phone number parsing, validation, and carrier intelligence."""

    def lookup_phone(self, phone: str) -> dict[str, Any]: ...


class NetworkLookupPort(Protocol):
    """Port for IP/Domain geolocation, DNS, and WHOIS lookups."""

    async def lookup_network_ioc(self, target: str) -> ProviderResult: ...


class EnrichmentProviderPort(Protocol):
    """Port for generic threat intelligence enrichment."""

    async def enrich(self, entity_type: str, value: str) -> ProviderResult: ...
