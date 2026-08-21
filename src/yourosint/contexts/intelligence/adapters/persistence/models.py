"""Intelligence Persistence ORM models."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class IntelligenceBase(DeclarativeBase):
    """Base ORM model for Intelligence context."""


class ObjectORM(IntelligenceBase):
    """Intelligence entity table."""

    __tablename__ = "objects"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    blind_index: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    masked_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    reputation: Mapped[int] = mapped_column(Integer, default=0, index=True)

    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="message")

    enrichment_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_enriched: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    evidence: Mapped[list["EvidenceORM"]] = relationship(
        "EvidenceORM", back_populates="object", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("type", "value", name="uq_objects_type_value"),
        Index("idx_objects_type_value", "type", "value"),
    )


class RelationORM(IntelligenceBase):
    """Entity relationship table."""

    __tablename__ = "relations"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    object1_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("objects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    object2_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("objects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    relation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="mentions", index=True
    )
    weight: Mapped[int] = mapped_column(Integer, default=1, index=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)

    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        UniqueConstraint(
            "object1_id", "object2_id", "relation_type", name="uq_relations_objects_type"
        ),
    )


class EvidenceORM(IntelligenceBase):
    """Provenance evidence table."""

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    object_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("objects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="message")
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_context: Mapped[str] = mapped_column(Text, nullable=False)

    chat_username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    chat_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=True
    )

    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    object: Mapped["ObjectORM"] = relationship("ObjectORM", back_populates="evidence")


class TimelineEventORM(IntelligenceBase):
    """Object timeline event history table."""

    __tablename__ = "object_timeline"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    object_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("objects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
