"""Command & Handler: Enrich Entity with External Providers."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from ....shared.application.command import Command, CommandHandler
from ....shared.domain.events import EntityEnriched, EventBus
from ..domain.provider_result import ProviderResult
from ..ports.provider import NetworkLookupPort, PhoneLookupPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EnrichEntityCommand(Command):
    entity_id: int
    entity_type: str
    value: str


class EnrichEntityHandler(CommandHandler[ProviderResult]):
    """Executes provider query and returns standardized enrichment payload."""

    def __init__(
        self,
        phone_lookup: PhoneLookupPort,
        network_lookup: NetworkLookupPort,
        event_bus: EventBus | None = None,
    ):
        self.phone_lookup = phone_lookup
        self.network_lookup = network_lookup
        self.event_bus = event_bus

    async def handle(self, cmd: EnrichEntityCommand) -> ProviderResult:
        logger.info(f"Enriching entity {cmd.entity_type}:{cmd.value} (ID: {cmd.entity_id})")

        if cmd.entity_type == "phone":
            data = self.phone_lookup.lookup_phone(cmd.value)
            res = ProviderResult(
                provider="phone_libphonenumber",
                target=cmd.value,
                is_valid=data.get("valid", False),
                risk_score=15 if data.get("valid") else 40,
                details=data,
            )
        elif cmd.entity_type in ["ip", "domain"]:
            res = await self.network_lookup.lookup_network_ioc(cmd.value)
        else:
            res = ProviderResult(
                provider="noop",
                target=cmd.value,
                is_valid=True,
                risk_score=0,
                details={},
            )

        if self.event_bus:
            await self.event_bus.publish(
                EntityEnriched(
                    event_id=f"enrich_{cmd.entity_id}_{int(datetime.now(UTC).timestamp())}",
                    entity_id=cmd.entity_id,
                    entity_type=cmd.entity_type,
                    reputation_score=res.risk_score,
                    provider_name=res.provider,
                )
            )

        return res
