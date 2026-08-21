"""Initial schema with PostgreSQL GIN indexes and pg_trgm extension.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-08-21 16:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable pg_trgm extension if on PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 2. Objects Table
    op.create_table(
        "objects",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("blind_index", sa.String(255), nullable=True),
        sa.Column("masked_value", sa.Text(), nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reputation", sa.Integer(), server_default="0"),
        sa.Column("tags", sa.JSON(), server_default="[]"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(50), server_default="message"),
        sa.Column("enrichment_data", sa.JSON(), server_default="{}"),
        sa.Column("last_enriched", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("type", "value", name="uq_objects_type_value"),
    )
    op.create_index("idx_objects_type", "objects", ["type"])
    op.create_index("idx_objects_blind_index", "objects", ["blind_index"])
    op.create_index("idx_objects_reputation", "objects", ["reputation"])

    # 3. Relations Table
    op.create_table(
        "relations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "object1_id",
            sa.BigInteger(),
            sa.ForeignKey("objects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "object2_id",
            sa.BigInteger(),
            sa.ForeignKey("objects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relation_type", sa.String(50), server_default="mentions", nullable=False),
        sa.Column("weight", sa.Integer(), server_default="1"),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "object1_id", "object2_id", "relation_type", name="uq_relations_objects_type"
        ),
    )
    op.create_index("idx_relations_obj1", "relations", ["object1_id"])
    op.create_index("idx_relations_obj2", "relations", ["object2_id"])
    op.create_index("idx_relations_type", "relations", ["relation_type"])

    # 4. Evidence Table
    op.create_table(
        "evidence",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "object_id",
            sa.BigInteger(),
            sa.ForeignKey("objects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(50), server_default="message", nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("raw_context", sa.Text(), nullable=False),
        sa.Column("chat_username", sa.String(255), nullable=True),
        sa.Column("chat_id", sa.String(255), nullable=True),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_evidence_object", "evidence", ["object_id"])
    op.create_index("idx_evidence_chat", "evidence", ["chat_username"])

    # 5. Messages Table
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_title", sa.String(255), nullable=True),
        sa.Column("chat_username", sa.String(255), nullable=True),
        sa.Column("sender_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_username", sa.String(255), nullable=True),
        sa.Column("sender_first_name", sa.String(255), nullable=True),
        sa.Column("sender_last_name", sa.String(255), nullable=True),
        sa.Column("message_text", sa.Text(), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("has_media", sa.Boolean(), server_default=sa.false()),
        sa.Column("media_type", sa.String(50), nullable=True),
        sa.Column("is_pii_filtered", sa.Boolean(), server_default=sa.false()),
        sa.UniqueConstraint("chat_id", "message_id", name="uq_messages_chat_message"),
    )
    op.create_index("idx_messages_chat", "messages", ["chat_id"])
    op.create_index("idx_messages_sender", "messages", ["sender_id"])
    op.create_index("idx_messages_chat_user", "messages", ["chat_username"])

    # 6. Monitored Chats Table
    op.create_table(
        "monitored_chats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(255), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=True),
        sa.Column("last_parsed_id", sa.BigInteger(), server_default="0"),
        sa.Column("total_messages", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("discovered_via", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 7. Telegram Accounts Table
    op.create_table(
        "telegram_accounts",
        sa.Column("name", sa.String(100), primary_key=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("ban_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chats_assigned", sa.JSON(), server_default="[]"),
        sa.Column("total_requests", sa.Integer(), server_default="0"),
        sa.Column("errors", sa.Integer(), server_default="0"),
        sa.Column("health_failures", sa.Integer(), server_default="0"),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
    )

    # 8. Object Timeline Table
    op.create_table(
        "object_timeline",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "object_id",
            sa.BigInteger(),
            sa.ForeignKey("objects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_data", sa.JSON(), server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_timeline_obj", "object_timeline", ["object_id"])

    # 9. Postgres GIN Indexes for Full-Text and Trigram Search
    if bind.dialect.name == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_text_trgm ON messages USING gin (message_text gin_trgm_ops);"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_user_trgm ON messages USING gin (sender_username gin_trgm_ops);"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_objects_value_trgm ON objects USING gin (value gin_trgm_ops);"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_fts ON messages USING gin (to_tsvector('russian', coalesce(message_text, '')));"
        )


def downgrade() -> None:
    op.drop_table("object_timeline")
    op.drop_table("telegram_accounts")
    op.drop_table("monitored_chats")
    op.drop_table("messages")
    op.drop_table("evidence")
    op.drop_table("relations")
    op.drop_table("objects")
