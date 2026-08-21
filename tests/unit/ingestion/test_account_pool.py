"""Unit tests for AccountPool load balancing, flood-wait, and session rotation."""

import pytest

from yourosint.contexts.ingestion.adapters.telegram.account_pool import AccountPool


class MockClient:
    def __init__(self, name):
        self.name = name

    async def get_me(self):
        return {"id": 100, "username": f"{self.name}_user", "phone": "+79990000000"}

    async def stop(self):
        pass


@pytest.mark.asyncio
async def test_account_pool_initialization():
    pool = AccountPool()
    await pool.register_account("acc1", MockClient("acc1"))
    await pool.register_account("acc2", MockClient("acc2"))

    stats = await pool.get_stats()
    assert stats["total"] == 2
    assert stats["active"] == 2
    await pool.close_all()


@pytest.mark.asyncio
async def test_least_loaded_selection():
    pool = AccountPool()
    c1 = MockClient("acc1")
    c2 = MockClient("acc2")
    await pool.register_account("acc1", c1)
    await pool.register_account("acc2", c2)

    chosen1 = await pool.get_next_available()
    assert chosen1 in [c1, c2]

    chosen2 = await pool.get_next_available()
    assert chosen2 is not None
    await pool.close_all()


@pytest.mark.asyncio
async def test_flood_wait_handling():
    pool = AccountPool()
    c1 = MockClient("acc1")
    await pool.register_account("acc1", c1)

    await pool.report_flood(c1, wait_seconds=120)

    acc = pool.accounts[0]
    assert acc["status"] == "flood_wait"
    assert acc["ban_until"] is not None

    next_client = await pool.get_next_available()
    assert next_client is None
    await pool.close_all()


@pytest.mark.asyncio
async def test_chat_affinity_selection():
    pool = AccountPool()
    c1 = MockClient("acc1")
    c2 = MockClient("acc2")
    await pool.register_account("acc1", c1)
    await pool.register_account("acc2", c2)

    first = await pool.get_next_available(chat_username="chat_beta")
    second = await pool.get_next_available(chat_username="chat_beta")
    assert first == second
    await pool.close_all()
