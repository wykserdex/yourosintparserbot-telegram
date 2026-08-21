"""Seed script for demo data in Bounded Contexts architecture."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from yourosint.bootstrap import container
from yourosint.contexts.ingestion.adapters.persistence.repositories import (
    SQLAlchemyChatRepository,
    SQLAlchemyMessageRepository,
)
from yourosint.contexts.ingestion.domain.chat import Chat
from yourosint.contexts.ingestion.domain.message import RawMessage
from yourosint.contexts.intelligence.adapters.persistence.repositories import (
    SQLAlchemyIntelligenceRepository,
)
from yourosint.contexts.intelligence.domain.entity import EntityType, IntelligenceEntity
from yourosint.contexts.intelligence.domain.relation import Relation, RelationType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


async def seed():
    logger.info("Seeding demo intelligence dataset...")
    await container.db.create_all_tables()

    async with container.db.session() as session:
        msg_repo = SQLAlchemyMessageRepository(session)
        chat_repo = SQLAlchemyChatRepository(session)
        intel_repo = SQLAlchemyIntelligenceRepository(session)

        # 1. Monitored Chats
        chats = [
            Chat(id=None, username="infosec_feed", title="Infosec Threat Feed"),
            Chat(id=None, username="osint_insider", title="OSINT Investigations"),
        ]
        for c in chats:
            await chat_repo.add_chat(c)

        # 2. Intelligence Entities
        durov = await intel_repo.upsert_entity(
            IntelligenceEntity(
                type=EntityType.USERNAME,
                value="durov",
                tags=["target", "vip"],
                description="Pavel Durov - Telegram Founder",
                reputation=10,
            )
        )
        ton = await intel_repo.upsert_entity(
            IntelligenceEntity(
                type=EntityType.DOMAIN,
                value="ton.org",
                tags=["crypto", "infrastructure"],
                description="The Open Network",
                reputation=5,
            )
        )
        await intel_repo.upsert_entity(
            IntelligenceEntity(
                type=EntityType.PHONE,
                value="79991234567",
                blind_index=container.blind_index_service.make_blind_index("79991234567").value,
                masked_value="+79 *** *** 4567",
                tags=["target_phone"],
                reputation=15,
            )
        )

        # 3. Relations
        if durov.id and ton.id:
            await intel_repo.save_relation(
                Relation(
                    source_entity_id=durov.id,
                    target_entity_id=ton.id,
                    relation_type=RelationType.CONTROLS,
                    weight=5,
                )
            )

        # 4. Messages
        now = datetime.now(UTC)
        msgs = [
            RawMessage(
                message_id=101,
                chat_id=9001,
                chat_title="Infosec Feed",
                chat_username="infosec_feed",
                sender_id=1,
                sender_username="durov",
                sender_first_name="Pavel",
                sender_last_name="Durov",
                text="Announcing major security update for Telegram v2",
                posted_at=now - timedelta(days=2),
            ),
            RawMessage(
                message_id=102,
                chat_id=9001,
                chat_title="Infosec Feed",
                chat_username="infosec_feed",
                sender_id=201,
                sender_username="investigator_mike",
                sender_first_name="Mike",
                sender_last_name="Pohomov",
                text="@durov reviewed the crypto architecture on ton.org",
                posted_at=now - timedelta(days=1),
            ),
            RawMessage(
                message_id=103,
                chat_id=9001,
                chat_title="Infosec Feed",
                chat_username="infosec_feed",
                sender_id=202,
                sender_username="analyst_jane",
                sender_first_name="Jane",
                sender_last_name="Doe",
                text="Confirmed zero-knowledge blind indexing integrity",
                posted_at=now - timedelta(hours=12),
            ),
        ]
        await msg_repo.bulk_save_messages(msgs)

    logger.info("Seeding completed successfully! ✨")


if __name__ == "__main__":
    asyncio.run(seed())
