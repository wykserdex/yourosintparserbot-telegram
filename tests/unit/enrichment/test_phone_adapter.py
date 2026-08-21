"""Unit tests for Phone Intelligence Adapter."""

from yourosint.contexts.enrichment.adapters.phone.phone_adapter import LibphonenumberAdapter


def test_phone_parsing():
    adapter = LibphonenumberAdapter()
    info = adapter.lookup_phone("+7 (999) 123-45-67")
    assert info["valid"] is True
    assert "e164" in info
    assert info["clean"] == "+79991234567"
    assert "messengers" in info
