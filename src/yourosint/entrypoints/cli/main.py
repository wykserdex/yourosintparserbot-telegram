"""Command Line Interface (CLI) Entrypoint."""

import asyncio
import sys

from yourosint.bootstrap import container
from yourosint.contexts.ingestion.adapters.persistence.repositories import (
    SQLAlchemyChatRepository,
    SQLAlchemyMessageRepository,
)
from yourosint.contexts.ingestion.application.commands.parse_chat import (
    ParseChatCommand,
    ParseChatHandler,
)

from ...config.logging import setup_logging


async def run_cli():
    setup_logging()
    if len(sys.argv) < 2:
        print("Usage: yourosint <command> [args...]")
        print("Commands: parse <chat_username> [limit]")
        return

    cmd = sys.argv[1]
    if cmd == "parse" and len(sys.argv) >= 3:
        chat = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 100
        await container.db.create_all_tables()

        async with container.db.session() as session:
            msg_repo = SQLAlchemyMessageRepository(session)
            chat_repo = SQLAlchemyChatRepository(session)
            handler = ParseChatHandler(
                account_pool=container.account_pool,
                message_repo=msg_repo,
                chat_repo=chat_repo,
                event_bus=container.event_bus,
            )
            res = await handler.handle(ParseChatCommand(chat_username=chat, limit=limit))
            print(
                f"✓ Parsed @{res.chat_username}: {res.messages_saved} msgs ({res.duration_seconds}s)"
            )
        await container.db.close()


def main():
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
