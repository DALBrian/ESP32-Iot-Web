"""Shared service helpers for telemetry ingestion."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Device, IngestError, Telemetry


def persist_telemetry(
    db: Session,
    *,
    device_id: str,
    ts: int,
    temperature: float,
    humidity: float,
) -> Telemetry:
    """Insert a telemetry record and ensure the device exists."""

    dev = db.execute(
        select(Device).where(Device.device_id == device_id)
    ).scalar_one_or_none()
    if not dev:
        dev = Device(device_id=device_id)
        db.add(dev)

    telemetry = Telemetry(
        device_id=device_id,
        ts=ts,
        temperature=temperature,
        humidity=humidity,
    )
    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)
    return telemetry


def record_ingest_error(
    db: Session, *, reason: str, device_id: str | None = None
) -> IngestError:
    """Persist an ingestion error for later inspection."""

    err = IngestError(device_id=device_id, reason=reason)
    db.add(err)
    db.commit()
    db.refresh(err)
    return err
