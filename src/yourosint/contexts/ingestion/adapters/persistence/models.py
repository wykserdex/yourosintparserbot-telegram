"""Ingestion persistence ORM models."""

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class IngestionBase(DeclarativeBase):
    """Base ORM model for Ingestion context."""


class MessageORM(IngestionBase):
    """Postgres / SQLite table for raw ingested messages."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    message_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=False
    )
    chat_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=False, index=True
    )
    chat_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chat_username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    sender_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=True, index=True
    )
    sender_username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    sender_first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    message_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    has_media: Mapped[bool] = mapped_column(Boolean, default=False)
    media_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_pii_filtered: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("chat_id", "message_id", name="uq_messages_chat_message"),
        Index("idx_messages_sender_chat", "sender_id", "chat_id"),
    )


class MonitoredChatORM(IngestionBase):
    """Monitored chats tracking cursor and status."""

    __tablename__ = "monitored_chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chat_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=True
    )
    last_parsed_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), default=0
    )
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    discovered_via: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class TelegramAccountORM(IngestionBase):
    """Worker session records in AccountPool."""

    __tablename__ = "telegram_accounts"

    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    ban_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    chats_assigned: Mapped[list[str]] = mapped_column(JSON, default=list)
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    health_failures: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
