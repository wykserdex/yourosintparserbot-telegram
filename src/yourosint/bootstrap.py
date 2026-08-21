"""Composition Root: Bootstrap and Dependency Injection Container."""

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from .config.feature_flags import FeatureFlags
from .config.settings import Settings, get_settings
from .contexts.enrichment.adapters.phone.phone_adapter import LibphonenumberAdapter
from .contexts.enrichment.adapters.threat_intel.network_adapter import NetworkThreatIntelAdapter
from .contexts.graph.adapters.networkx.engine import NetworkXGraphEngine
from .contexts.graph.ports.graph_engine import GraphEnginePort, GraphQueryPort
from .contexts.ingestion.adapters.telegram.account_pool import AccountPool
from .contexts.ingestion.adapters.telegram.client import SmartTelegramClient
from .contexts.intelligence.adapters.extractors.regex_extractor import RegexEntityExtractor
from .contexts.privacy.adapters.hmac_blind_index import HMACBlindIndexService
from .contexts.privacy.adapters.key_store.env_key_store import EnvKeyStore
from .infrastructure.database.session import DatabaseSessionManager
from .shared.domain.events import InMemoryEventBus

logger = logging.getLogger(__name__)


class SqlAlchemyGraphQueryAdapter(GraphQueryPort):
    """Executes single-query SQL CTEs for graph interaction analysis."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def query_user_interactions(
        self, target_username: str, limit: int = 200
    ) -> list[dict[str, Any]]:
        clean_username = target_username.lstrip("@").strip().lower()
        bind = self.session.bind
        dialect_name = bind.dialect.name if bind else "postgresql"

        if dialect_name == "sqlite":
            query_sql = text("""
                WITH target_ids AS (
                    SELECT DISTINCT sender_id, sender_username, sender_first_name, sender_last_name
                    FROM messages
                    WHERE (sender_username LIKE :target_pattern OR message_text LIKE :target_pattern)
                      AND sender_id IS NOT NULL
                    LIMIT 10
                ),
                all_users AS (
                    SELECT
                        m.sender_id AS user_id,
                        t.sender_id AS target_id,
                        t.sender_username AS target_username,
                        t.sender_first_name AS target_first_name,
                        t.sender_last_name AS target_last_name,
                        m.sender_username AS user_username,
                        m.sender_first_name AS user_first_name,
                        m.sender_last_name AS user_last_name,
                        m.chat_id
                    FROM messages m
                    JOIN target_ids t ON m.chat_id IN (
                        SELECT DISTINCT chat_id FROM messages WHERE sender_id = t.sender_id
                    )
                    WHERE m.sender_id != t.sender_id AND m.sender_id IS NOT NULL
                )
                SELECT
                    user_id,
                    target_id,
                    target_username,
                    target_first_name,
                    target_last_name,
                    user_username,
                    user_first_name,
                    user_last_name,
                    COUNT(*) AS total_interactions,
                    COUNT(DISTINCT chat_id) AS total_common_chats
                FROM all_users
                GROUP BY user_id, target_id, target_username, target_first_name, target_last_name,
                         user_username, user_first_name, user_last_name
                ORDER BY total_interactions DESC
                LIMIT :lim
            """)
        else:
            query_sql = text("""
                WITH target_ids AS (
                    SELECT DISTINCT sender_id, sender_username, sender_first_name, sender_last_name
                    FROM messages
                    WHERE sender_username ILIKE :target_pattern
                       OR message_text ILIKE :target_pattern
                    ORDER BY sender_id
                    LIMIT 10
                ),
                all_users AS (
                    SELECT DISTINCT
                        m.sender_id as user_id,
                        t.sender_id as target_id,
                        t.sender_username as target_username,
                        t.sender_first_name as target_first_name,
                        t.sender_last_name as target_last_name,
                        m.chat_id,
                        COUNT(*) OVER (PARTITION BY m.sender_id, t.sender_id) as interaction_weight
                    FROM messages m
                    CROSS JOIN target_ids t
                    WHERE m.chat_id IN (
                        SELECT DISTINCT chat_id
                        FROM messages
                        WHERE sender_id = t.sender_id
                    )
                    AND m.sender_id != t.sender_id
                    AND m.sender_id IS NOT NULL
                ),
                enriched_users AS (
                    SELECT
                        u.user_id,
                        u.target_id,
                        u.target_username,
                        u.target_first_name,
                        u.target_last_name,
                        u.interaction_weight,
                        COALESCE(m2.sender_username, '') as user_username,
                        COALESCE(m2.sender_first_name, '') as user_first_name,
                        COALESCE(m2.sender_last_name, '') as user_last_name,
                        COUNT(DISTINCT u.chat_id) as common_chats
                    FROM all_users u
                    LEFT JOIN LATERAL (
                        SELECT sender_username, sender_first_name, sender_last_name
                        FROM messages
                        WHERE sender_id = u.user_id
                        LIMIT 1
                    ) m2 ON true
                    GROUP BY u.user_id, u.target_id, u.target_username, u.target_first_name,
                             u.target_last_name, u.interaction_weight, m2.sender_username,
                             m2.sender_first_name, m2.sender_last_name
                )
                SELECT
                    user_id,
                    target_id,
                    target_username,
                    target_first_name,
                    target_last_name,
                    user_username,
                    user_first_name,
                    user_last_name,
                    SUM(interaction_weight) as total_interactions,
                    SUM(common_chats) as total_common_chats
                FROM enriched_users
                GROUP BY user_id, target_id, target_username, target_first_name, target_last_name,
                         user_username, user_first_name, user_last_name
                ORDER BY total_interactions DESC
                LIMIT :lim
            """)

        res = await self.session.execute(
            query_sql,
            {"target_pattern": f"%{clean_username}%", "lim": limit},
        )
        return [dict(r) for r in res.mappings().all()]

    async def query_second_level_connections(
        self, contact_ids: list[int], limit: int = 500
    ) -> list[dict[str, Any]]:
        if len(contact_ids) < 2:
            return []

        bind = self.session.bind
        dialect_name = bind.dialect.name if bind else "postgresql"

        if dialect_name == "sqlite":
            query_sql = text("""
                SELECT
                    m1.sender_id AS user1_id,
                    m2.sender_id AS user2_id,
                    COUNT(DISTINCT m1.chat_id) AS common_chats
                FROM messages m1
                JOIN messages m2 ON m1.chat_id = m2.chat_id AND m1.sender_id < m2.sender_id
                WHERE m1.sender_id IN :c_ids AND m2.sender_id IN :c_ids
                GROUP BY m1.sender_id, m2.sender_id
                HAVING COUNT(DISTINCT m1.chat_id) > 0
                ORDER BY common_chats DESC
                LIMIT :lim
            """).bindparams(bindparam("c_ids", expanding=True))
            res = await self.session.execute(
                query_sql,
                {"c_ids": list(contact_ids), "lim": limit},
            )
        else:
            query_sql = text("""
                WITH contact_chats AS (
                    SELECT
                        sender_id,
                        array_agg(DISTINCT chat_id) as chats
                    FROM messages
                    WHERE sender_id = ANY(:c_ids)
                    GROUP BY sender_id
                )
                SELECT
                    c1.sender_id as user1_id,
                    c2.sender_id as user2_id,
                    (
                        SELECT COUNT(*)
                        FROM unnest(c1.chats) AS u1
                        WHERE u1 = ANY(c2.chats)
                    ) as common_chats
                FROM contact_chats c1
                JOIN contact_chats c2 ON c1.sender_id < c2.sender_id
                HAVING (
                    SELECT COUNT(*)
                    FROM unnest(c1.chats) AS u1
                    WHERE u1 = ANY(c2.chats)
                ) > 0
                ORDER BY common_chats DESC
                LIMIT :lim
            """)
            res = await self.session.execute(
                query_sql,
                {"c_ids": contact_ids, "lim": limit},
            )

        return [dict(r) for r in res.mappings().all()]


@dataclass
class Container:
    """Dependency Injection Container."""

    settings: Settings
    flags: FeatureFlags
    db: DatabaseSessionManager
    event_bus: InMemoryEventBus
    account_pool: AccountPool
    blind_index_service: HMACBlindIndexService
    key_store: EnvKeyStore
    phone_lookup: LibphonenumberAdapter
    network_lookup: NetworkThreatIntelAdapter
    regex_extractor: RegexEntityExtractor
    graph_engine: GraphEnginePort


def create_container(settings: Settings | None = None) -> Container:
    """Assembles all bounded contexts and adapters into a unified composition root."""
    active_settings = settings or get_settings()
    flags = FeatureFlags()

    db = DatabaseSessionManager(active_settings)
    event_bus = InMemoryEventBus()
    account_pool = AccountPool()
    account_pool.accounts.append(
        {
            "name": "primary_worker",
            "client": SmartTelegramClient(session_name="primary_worker"),
            "phone": "+79991234567",
            "username": "yourosint_worker",
            "status": "active",
            "ban_until": None,
            "chats_assigned": [],
            "total_requests": 0,
            "last_used": None,
            "errors": 0,
            "health_check_failures": 0,
        }
    )

    key_store = EnvKeyStore(
        active_settings.BLIND_INDEX_KEY, active_settings.BLIND_INDEX_KEY_VERSION
    )
    blind_index_service = HMACBlindIndexService(
        active_settings.BLIND_INDEX_KEY, active_settings.BLIND_INDEX_KEY_VERSION
    )

    phone_lookup = LibphonenumberAdapter()
    network_lookup = NetworkThreatIntelAdapter(
        virustotal_key=active_settings.VIRUSTOTAL_API_KEY,
        abuseipdb_key=active_settings.ABUSEIPDB_API_KEY,
    )
    regex_extractor = RegexEntityExtractor()
    graph_engine = NetworkXGraphEngine()

    return Container(
        settings=active_settings,
        flags=flags,
        db=db,
        event_bus=event_bus,
        account_pool=account_pool,
        blind_index_service=blind_index_service,
        key_store=key_store,
        phone_lookup=phone_lookup,
        network_lookup=network_lookup,
        regex_extractor=regex_extractor,
        graph_engine=graph_engine,
    )


# Global singleton container instance
container = create_container()
