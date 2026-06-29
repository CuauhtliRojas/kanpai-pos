from datetime import datetime
from app.core.time import local_now_naive
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped

from app.core.database import Base
from app.domain.database_contract import db_column
from app.domain.constants import (
    SyncStatus,
)


class SyncInbox(Base):
    __tablename__ = "bandeja_entrada_sincronizacion"
    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "airtable_record_id",
            "remote_revision",
            name="uq_sync_inbox_remote_revision",
        ),
    )

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    source: Mapped[str] = db_column(
        "source", String(64), default="AIRTABLE", nullable=False
    )
    entity_type: Mapped[str] = db_column("entity_type", String(80), nullable=False)
    airtable_record_id: Mapped[str] = db_column(
        "airtable_record_id", String(64), nullable=False
    )
    remote_revision: Mapped[str] = db_column(
        "remote_revision", String(128), nullable=False
    )
    payload_json: Mapped[str] = db_column("payload_json", Text, nullable=False)
    status: Mapped[str] = db_column(
        "status", String(32), default=SyncStatus.PENDING, nullable=False
    )
    error: Mapped[Optional[str]] = db_column("error", Text)
    received_at: Mapped[datetime] = db_column(
        "received_at", DateTime, default=local_now_naive, nullable=False
    )
    applied_at: Mapped[Optional[datetime]] = db_column("applied_at", DateTime)


class SyncOutbox(Base):
    __tablename__ = "bandeja_salida_sincronizacion"
    __table_args__ = (UniqueConstraint("event_id", name="uq_sync_outbox_event_id"),)

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    event_id: Mapped[str] = db_column("event_id", String(128), nullable=False)
    aggregate_type: Mapped[str] = db_column(
        "aggregate_type", String(80), nullable=False
    )
    aggregate_id: Mapped[str] = db_column("aggregate_id", String(80), nullable=False)
    event_type: Mapped[str] = db_column("event_type", String(120), nullable=False)
    payload_version: Mapped[str] = db_column(
        "payload_version", String(32), default="v1", nullable=False
    )
    payload_json: Mapped[str] = db_column("payload_json", Text, nullable=False)
    status: Mapped[str] = db_column(
        "status", String(32), default=SyncStatus.PENDING, nullable=False
    )
    attempts: Mapped[int] = db_column("attempts", Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = db_column("last_error", Text)
    airtable_record_id: Mapped[Optional[str]] = db_column(
        "airtable_record_id", String(64)
    )
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=local_now_naive, nullable=False
    )
    sent_at: Mapped[Optional[datetime]] = db_column("sent_at", DateTime)


class SyncWatermark(Base):
    __tablename__ = "marcas_agua_sincronizacion"
    __table_args__ = (
        UniqueConstraint("entity_type", name="uq_sync_watermark_entity_type"),
    )

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    entity_type: Mapped[str] = db_column("entity_type", String(80), nullable=False)
    last_successful_pull_at: Mapped[Optional[datetime]] = db_column(
        "last_successful_pull_at", DateTime
    )
    last_successful_push_at: Mapped[Optional[datetime]] = db_column(
        "last_successful_push_at", DateTime
    )
    last_remote_cursor: Mapped[Optional[str]] = db_column(
        "last_remote_cursor", String(255)
    )
    status: Mapped[str] = db_column(
        "status", String(32), default=SyncStatus.IDLE, nullable=False
    )
    updated_at: Mapped[datetime] = db_column(
        "updated_at",
        DateTime,
        default=local_now_naive,
        onupdate=local_now_naive,
        nullable=False,
    )
