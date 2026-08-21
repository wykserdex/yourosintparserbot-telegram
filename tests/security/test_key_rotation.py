"""Security test suite: Cryptographic Key Rotation."""

from yourosint.contexts.privacy.adapters.hmac_blind_index import HMACBlindIndexService


def test_key_rotation_isolation():
    service = HMACBlindIndexService(key="key-v1", version="v1")
    old_idx, new_idx = service.rotate_blind_index(
        normalized_value="target@domain.org",
        old_key=b"key-v1",
        new_key=b"key-v2",
        old_version="v1",
        new_version="v2",
    )

    assert old_idx.version == "v1"
    assert new_idx.version == "v2"
    assert old_idx.digest != new_idx.digest
