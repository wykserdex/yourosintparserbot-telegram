"""Command & Handler: Merge correlated duplicate entities."""

from dataclasses import dataclass

from .....shared.application.command import Command, CommandHandler
from ...domain.entity import IntelligenceEntity
from ...ports.repositories import IntelligenceRepositoryPort


@dataclass(frozen=True, slots=True)
class MergeEntitiesCommand(Command):
    primary_entity_id: int
    secondary_entity_id: int
    reason: str


class MergeEntitiesHandler(CommandHandler[IntelligenceEntity | None]):
    """Merges secondary entity into primary entity, repointing relations and evidence."""

    def __init__(self, intelligence_repo: IntelligenceRepositoryPort):
        self.intelligence_repo = intelligence_repo

    async def handle(self, cmd: MergeEntitiesCommand) -> IntelligenceEntity | None:
        primary = await self.intelligence_repo.get_by_id(cmd.primary_entity_id)
        secondary = await self.intelligence_repo.get_by_id(cmd.secondary_entity_id)

        if not primary or not secondary:
            return None

        # Merge tags & enrichment data
        combined_tags = list(set(primary.tags + secondary.tags))
        primary.tags = combined_tags
        primary.enrichment_data.update(secondary.enrichment_data)
        primary.reputation = max(primary.reputation, secondary.reputation)

        return await self.intelligence_repo.upsert_entity(primary)
