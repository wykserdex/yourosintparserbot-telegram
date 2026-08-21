"""Contract tests for Threat Intel and GeoIP adapters."""

import pytest

from yourosint.contexts.enrichment.adapters.phone.phone_adapter import LibphonenumberAdapter
from yourosint.contexts.enrichment.adapters.threat_intel.network_adapter import (
    NetworkThreatIntelAdapter,
)
from yourosint.contexts.enrichment.domain.provider_result import ProviderResult


@pytest.mark.asyncio
async def test_network_threat_intel_contract():
    adapter = NetworkThreatIntelAdapter()
    res = await adapter.lookup_network_ioc("8.8.8.8")
    assert isinstance(res, ProviderResult)
    assert res.target == "8.8.8.8"
    assert res.is_valid is True
    assert "is_ip" in res.details
    assert res.details["is_ip"] is True


def test_phone_adapter_contract():
    adapter = LibphonenumberAdapter()
    info = adapter.lookup_phone("+14155552671")
    assert isinstance(info, dict)
    assert info["valid"] is True
    assert info["clean"] == "+14155552671"
