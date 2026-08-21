"""Unit tests for RegexEntityExtractor."""

import pytest

from yourosint.contexts.intelligence.adapters.extractors.regex_extractor import RegexEntityExtractor
from yourosint.contexts.intelligence.domain.entity import EntityType


@pytest.fixture
def extractor():
    return RegexEntityExtractor()


def test_extract_emails(extractor):
    text = "Reports sent to analyst@secops.io and alerts@cyberdefense.com"
    res = extractor.extract_all(text)
    assert EntityType.EMAIL in res
    assert "analyst@secops.io" in res[EntityType.EMAIL]
    assert "alerts@cyberdefense.com" in res[EntityType.EMAIL]


def test_extract_domains(extractor):
    text = "Check threat portal https://malicious-c2.net/gate and evil-payload.ru"
    res = extractor.extract_all(text)
    assert EntityType.DOMAIN in res
    assert "malicious-c2.net" in res[EntityType.DOMAIN]
    assert "evil-payload.ru" in res[EntityType.DOMAIN]


def test_extract_public_ips_and_filter_private(extractor):
    text = "Attacker IP: 185.220.101.5, internal LAN: 192.168.1.1, loopback: 127.0.0.1"
    res = extractor.extract_all(text)
    assert EntityType.IP in res
    assert "185.220.101.5" in res[EntityType.IP]
    assert "192.168.1.1" not in res[EntityType.IP]
    assert "127.0.0.1" not in res[EntityType.IP]


def test_extract_phones(extractor):
    text = "Call target at +7 (999) 123-45-67 or 89261234567"
    res = extractor.extract_all(text)
    assert EntityType.PHONE in res
    assert "79991234567" in res[EntityType.PHONE]
    assert "79261234567" in res[EntityType.PHONE]


def test_extract_crypto_wallets(extractor):
    text = "BTC wallet: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa ETH wallet: 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    res = extractor.extract_all(text)
    assert EntityType.CRYPTO_BTC in res
    assert "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" in res[EntityType.CRYPTO_BTC]
    assert EntityType.CRYPTO_ETH in res
    assert "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" in res[EntityType.CRYPTO_ETH]
