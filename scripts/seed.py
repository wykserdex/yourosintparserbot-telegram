"""Seed database with realistic demo OSINT data and targets."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from yourosint.domain.entities import Message, MonitoredChat, Object, Relation
from yourosint.domain.enums import ObjectType, RelationType
from yourosint.infrastructure.persistence.database import db_manager
from yourosint.infrastructure.persistence.repositories import (
    ChatRepository,
    MessageRepository,
    ObjectStoreRepository,
)
from yourosint.infrastructure.privacy.blind_index import BlindIndexService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


async def seed_data():
    logger.info("Seeding demo intelligence dataset...")
    await db_manager.create_all_tables()

    async with db_manager.session() as session:
        obj_repo = ObjectStoreRepository(session)
        msg_repo = MessageRepository(session)
        chat_repo = ChatRepository(session)
        blind_service = BlindIndexService(key="demo-seed-key")

        # 1. Monitored Chats
        chats = [
            MonitoredChat(username="infosec_feed", title="Infosec Threat Feed", is_active=True),
            MonitoredChat(username="osint_insider", title="OSINT Investigations", is_active=True),
            MonitoredChat(
                username="crypto_scam_tracker", title="Crypto Scam Alerts", is_active=True
            ),
        ]
        for c in chats:
            await chat_repo.add_chat(c)

        # 2. Objects & IOCs
        entities = [
            Object(
                type=ObjectType.USERNAME,
                value="durov",
                tags=["target", "vip"],
                description="Pavel Durov - Telegram Founder",
                reputation=10,
            ),
            Object(
                type=ObjectType.DOMAIN,
                value="ton.org",
                tags=["crypto", "infrastructure"],
                description="The Open Network official domain",
                reputation=5,
            ),
            Object(
                type=ObjectType.EMAIL,
                value="contact@durov.im",
                blind_index=blind_service.make_blind_index("contact@durov.im").value,
                masked_value=blind_service.mask_value("contact@durov.im", ObjectType.EMAIL),
                tags=["verified"],
                reputation=0,
            ),
            Object(
                type=ObjectType.PHONE,
                value="79991234567",
                blind_index=blind_service.make_blind_index("79991234567").value,
                masked_value=blind_service.mask_value("79991234567", ObjectType.PHONE),
                tags=["target_phone"],
                reputation=15,
            ),
            Object(
                type=ObjectType.CARD,
                value="4276123456788821",
                blind_index=blind_service.make_blind_index("4276123456788821").value,
                masked_value=blind_service.mask_value("4276123456788821", ObjectType.CARD),
                tags=["financial_ioc"],
                reputation=75,
            ),
            Object(
                type=ObjectType.CRYPTO_BTC,
                value="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                tags=["crypto", "genesis_block"],
                reputation=0,
            ),
        ]

        saved_objects = []
        for e in entities:
            saved = await obj_repo.create_object(e)
            saved_objects.append(saved)

        # 3. Relations
        if len(saved_objects) >= 3:
            await obj_repo.create_relation(
                Relation(
                    object1_id=saved_objects[0].id,
                    object2_id=saved_objects[1].id,
                    relation_type=RelationType.CONTROLS,
                    weight=5,
                    context="Found in channel announcements",
                )
            )
            await obj_repo.create_relation(
                Relation(
                    object1_id=saved_objects[0].id,
                    object2_id=saved_objects[2].id,
                    relation_type=RelationType.USES,
                    weight=3,
                    context="Verified contact email",
                )
            )

        # 4. Messages for Target interaction CTE graph
        now = datetime.now(UTC)
        messages = [
            Message(
                message_id=101,
                chat_id=9001,
                chat_title="Infosec Feed",
                chat_username="infosec_feed",
                sender_id=1,
                sender_username="durov",
                sender_first_name="Pavel",
                sender_last_name="Durov",
                message_text="Announcing major security update for Telegram v2",
                date=now - timedelta(days=2),
            ),
            Message(
                message_id=102,
                chat_id=9001,
                chat_title="Infosec Feed",
                chat_username="infosec_feed",
                sender_id=201,
                sender_username="investigator_mike",
                sender_first_name="Mike",
                sender_last_name="Pohomov",
                message_text="@durov reviewed the crypto architecture on ton.org",
                date=now - timedelta(days=1),
            ),
            Message(
                message_id=103,
                chat_id=9001,
                chat_title="Infosec Feed",
                chat_username="infosec_feed",
                sender_id=202,
                sender_username="analyst_jane",
                sender_first_name="Jane",
                sender_last_name="Doe",
                message_text="Confirmed zero-knowledge blind indexing integrity",
                date=now - timedelta(hours=12),
            ),
            Message(
                message_id=104,
                chat_id=9002,
                chat_title="OSINT Insider",
                chat_username="osint_insider",
                sender_id=1,
                sender_username="durov",
                sender_first_name="Pavel",
                sender_last_name="Durov",
                message_text="Privacy by design is non-negotiable.",
                date=now - timedelta(hours=6),
            ),
            Message(
                message_id=105,
                chat_id=9002,
                chat_title="OSINT Insider",
                chat_username="osint_insider",
                sender_id=201,
                sender_username="investigator_mike",
                sender_first_name="Mike",
                sender_last_name="Pohomov",
                message_text="Analyzing user graph with CTE speed.",
                date=now - timedelta(hours=2),
            ),
        ]

        await msg_repo.bulk_save_messages(messages)

    logger.info("Demo seeding completed successfully! ✨")


if __name__ == "__main__":
    asyncio.run(seed_data())
