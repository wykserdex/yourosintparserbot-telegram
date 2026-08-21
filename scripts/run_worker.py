"""Worker execution script for running autopilot and enrichment."""

import asyncio
import contextlib
import logging
import signal

from yourosint.application.use_cases.discover_chats import DiscoverChatsUseCase
from yourosint.application.use_cases.enrich_entity import EnrichEntityUseCase
from yourosint.application.use_cases.extract_objects import ExtractObjectsUseCase
from yourosint.application.use_cases.parse_chat import ParseChatUseCase
from yourosint.config import get_settings
from yourosint.infrastructure.persistence.database import db_manager
from yourosint.infrastructure.persistence.repositories import (
    ChatRepository,
    MessageRepository,
    ObjectStoreRepository,
)
from yourosint.infrastructure.privacy.blind_index import BlindIndexService
from yourosint.infrastructure.telegram.account_pool import AccountPool
from yourosint.workers.autopilot import AutopilotWorker
from yourosint.workers.enrichment import BackgroundEnrichmentWorker

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("worker")


async def main():
    settings = get_settings()
    logger.info("Initializing Yourosint v2 Workers...")

    await db_manager.create_all_tables()
    pool = AccountPool()
    await pool.register_account(
        "worker_node_1", None, phone="+79990000001", username="yourosint_worker"
    )

    async with db_manager.session() as session:
        chat_repo = ChatRepository(session)
        msg_repo = MessageRepository(session)
        obj_store = ObjectStoreRepository(session)
        blind_service = BlindIndexService(
            settings.BLIND_INDEX_KEY, settings.BLIND_INDEX_KEY_VERSION
        )

        extractor = ExtractObjectsUseCase(object_store=obj_store, blind_index_service=blind_service)
        disc_use_case = DiscoverChatsUseCase(account_pool=pool, chat_repo=chat_repo)
        parse_use_case = ParseChatUseCase(
            account_pool=pool,
            message_repo=msg_repo,
            chat_repo=chat_repo,
            extractor=extractor,
        )
        enrich_use_case = EnrichEntityUseCase(object_store=obj_store)

        autopilot = AutopilotWorker(
            discover_use_case=disc_use_case,
            parse_use_case=parse_use_case,
            chat_repo=chat_repo,
        )
        enrichment_worker = BackgroundEnrichmentWorker(
            object_store=obj_store,
            enrich_use_case=enrich_use_case,
        )

        await autopilot.start()
        await enrichment_worker.start()

        logger.info("Workers are active. Press Ctrl+C to terminate.")

        stop_event = asyncio.Event()

        def stop():
            stop_event.set()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            with contextlib.suppress(NotImplementedError):
                loop.add_signal_handler(sig, stop)

        await stop_event.wait()

        await autopilot.stop()
        await enrichment_worker.stop()
        await pool.close_all()
        await db_manager.close()
        logger.info("Workers shutdown cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
