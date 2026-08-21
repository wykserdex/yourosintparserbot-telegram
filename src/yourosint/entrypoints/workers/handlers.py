"""Asynchronous Domain Event Handlers connecting Bounded Contexts."""

import logging

from yourosint.bootstrap import Container
from yourosint.contexts.intelligence.adapters.persistence.repositories import (
    SQLAlchemyIntelligenceRepository,
)
from yourosint.contexts.intelligence.application.commands.extract_entities import (
    ExtractEntitiesCommand,
    ExtractEntitiesHandler,
)
from yourosint.shared.domain.events import MessageImported

logger = logging.getLogger(__name__)


def register_event_handlers(c: Container) -> None:
    """Registers reactive domain event subscribers."""

    async def handle_message_imported(event: MessageImported) -> None:
        logger.debug(
            f"Event MessageImported received: msg #{event.message_id} in @{event.chat_username}"
        )
        async with c.db.session() as session:
            intel_repo = SQLAlchemyIntelligenceRepository(session)
            handler = ExtractEntitiesHandler(
                extractor=c.regex_extractor,
                intelligence_repo=intel_repo,
                blind_index_port=c.blind_index_service,
                event_bus=c.event_bus,
            )
            await handler.handle(
                ExtractEntitiesCommand(
                    text=event.text_content,
                    source_id=f"{event.chat_id}_{event.message_id}",
                    source_type="message",
                    chat_username=event.chat_username,
                    chat_id=str(event.chat_id),
                    message_id=event.message_id,
                )
            )

    c.event_bus.subscribe(MessageImported, handle_message_imported)
    logger.info("Registered reactive Domain Event handlers")
