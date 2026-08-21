"""Security test suite: Prevent plain-text PII storage leaks."""

from yourosint.contexts.privacy.adapters.hmac_blind_index import HMACBlindIndexService


def test_blind_index_no_plaintext_leak():
    service = HMACBlindIndexService(key="top-secret-salt-key")
    phone = "+7 (999) 123-45-67"
    norm_phone = service.normalize_phone(phone)
    blind_idx = service.make_blind_index(norm_phone)

    # Assert raw digits do not appear in hash digest
    assert "9991234567" not in blind_idx.value
    assert "79991234567" not in blind_idx.value
    assert len(blind_idx.digest) == 64
