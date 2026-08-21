"""Unit tests for privacy retention policy and key rotation use cases."""

from datetime import timedelta

import pytest

from yourosint.contexts.privacy.adapters.hmac_blind_index import HMACBlindIndexService
from yourosint.contexts.privacy.adapters.key_store.env_key_store import EnvKeyStore
from yourosint.contexts.privacy.application.build_blind_index import (
    BuildBlindIndexCommand,
    BuildBlindIndexHandler,
)
from yourosint.contexts.privacy.application.rotate_keys import RotateKeysHandler
from yourosint.contexts.privacy.domain.policy import DataRetentionPolicy


def test_retention_policy_defaults():
    policy = DataRetentionPolicy()
    assert policy.raw_message_retention == timedelta(days=90)
    assert policy.evidence_retention == timedelta(days=365)
    assert policy.anonymize_after_retention is True


@pytest.mark.asyncio
async def test_build_blind_index_handler():
    service = HMACBlindIndexService(key="test-key-2026")
    handler = BuildBlindIndexHandler(blind_index_port=service)

    val = await handler.handle(
        BuildBlindIndexCommand(value="  Contact@Threat.im ", entity_type="email")
    )
    assert val.version == "v1"
    assert len(val.digest) == 64


@pytest.mark.asyncio
async def test_rotate_keys_handler():
    key_store = EnvKeyStore(key="old-key-v1", version="v1")
    service = HMACBlindIndexService(key="old-key-v1", version="v1")
    handler = RotateKeysHandler(blind_index_port=service, key_store=key_store)

    old_idx, new_idx = await handler.handle_rotation(
        normalized_value="79991234567",
        new_version="v2",
        new_key=b"new-key-v2",
    )
    assert old_idx.version == "v1"
    assert new_idx.version == "v2"
    assert old_idx.digest != new_idx.digest
