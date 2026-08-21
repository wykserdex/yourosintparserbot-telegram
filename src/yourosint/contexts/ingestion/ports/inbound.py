"""Ingestion Ports: Inbound Gateway."""

from typing import Protocol

from ..domain.message import RawMessage


class InboundGatewayPort(Protocol):
    """Port for receiving messages from webhooks or direct imports."""

    async def ingest_raw_message(self, message: RawMessage) -> bool: ...
