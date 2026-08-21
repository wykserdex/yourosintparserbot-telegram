"""End-to-End Investigation Flow test."""

import pytest
from httpx import ASGITransport, AsyncClient

from yourosint.entrypoints.api.app import app
from yourosint.entrypoints.api.dependencies import get_db_session


@pytest.fixture(autouse=True)
def override_api_session(db_session):
    async def _test_session():
        yield db_session

    app.dependency_overrides[get_db_session] = _test_session
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_full_investigation_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        h_resp = await client.get("/api/v1/health")
        assert h_resp.status_code == 200

        # 2. Stats
        s_resp = await client.get("/api/v1/stats")
        assert s_resp.status_code == 200

        # 3. Ingest sample chat
        parse_resp = await client.post(
            "/api/v1/ingestion/parse",
            json={"chat_username": "cyber_threat_channel", "limit": 10},
        )
        assert parse_resp.status_code == 200
        assert parse_resp.json()["messages_saved"] >= 1

        # 4. Search intelligence
        search_resp = await client.get("/api/v1/intelligence/search?q=target")
        assert search_resp.status_code == 200
        data = search_resp.json()
        assert "entities" in data
        assert "messages" in data
