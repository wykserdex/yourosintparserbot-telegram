"""Unit tests for HMAC Blind Index Service."""

from yourosint.contexts.privacy.adapters.hmac_blind_index import HMACBlindIndexService


def test_blind_index_deterministic_hashing():
    service = HMACBlindIndexService(key="secret-salt-2026", version="v1")
    idx1 = service.make_blind_index("test@secops.io")
    idx2 = service.make_blind_index("test@secops.io")

    assert idx1.value == idx2.value
    assert idx1.version == "v1"
    assert len(idx1.digest) == 64


def test_blind_index_masking():
    service = HMACBlindIndexService(key="test-key")
    assert service.mask_value("4276123456788821", "card") == "**** **** **** 8821"
    assert service.mask_value("+79991234567", "phone") == "+79 *** *** 4567"
    assert service.mask_value("alice@example.com", "email") == "a***@example.com"
