from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SyncInbox(Base):
    __tablename__ = "sync_inbox"
    __table_args__ = (
        UniqueConstraint("entity_type", "airtable_record_id", "remote_revision", name="uq_sync_inbox_remote_revision"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(64), default="AIRTABLE", nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    airtable_record_id: Mapped[str] = mapped_column(String(64), nullable=False)
    remote_revision: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class SyncOutbox(Base):
    __tablename__ = "sync_outbox"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_sync_outbox_event_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(80), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    airtable_record_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class SyncWatermark(Base):
    __tablename__ = "sync_watermarks"
    __table_args__ = (
        UniqueConstraint("entity_type", name="uq_sync_watermark_entity_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    last_successful_pull_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_successful_push_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_remote_cursor: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="IDLE", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
