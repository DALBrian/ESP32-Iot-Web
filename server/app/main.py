"""FastAPI entrypoint for the IoT backend."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import IngestError, Telemetry
from .mqtt import mqtt_service
from .services import persist_telemetry
from .settings import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="IoT Telemetry Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TelemetryIn(BaseModel):
    deviceId: str
    ts: int
    temperature: float
    humidity: float


ONLINE_DELTA = timedelta(seconds=settings.ONLINE_GRACE_SECONDS)


def _to_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def _resolve_device(device_id: Optional[str]) -> str:
    return device_id or settings.DEFAULT_DEVICE_ID


@app.on_event("startup")
def _startup() -> None:
    mqtt_service.start()


@app.on_event("shutdown")
def _shutdown() -> None:
    mqtt_service.stop()


@app.post("/ingest")
def ingest(t: TelemetryIn, db: Session = Depends(get_db)):
    persist_telemetry(
        db,
        device_id=t.deviceId,
        ts=t.ts,
        temperature=t.temperature,
        humidity=t.humidity,
    )
    return {"ok": True}


@app.get("/latest")
def latest(deviceId: Optional[str] = None, db: Session = Depends(get_db)):
    device_id = _resolve_device(deviceId)
    row = (
        db.execute(
            select(Telemetry)
            .where(Telemetry.device_id == device_id)
            .order_by(desc(Telemetry.ts))
            .limit(1)
        )
        .scalar_one_or_none()
    )
    if not row:
        raise HTTPException(status_code=404, detail="no data")

    ts_iso = _to_iso(row.ts)
    now = datetime.now(tz=timezone.utc)
    is_online = now - datetime.fromtimestamp(
        row.ts, tz=timezone.utc
    ) <= ONLINE_DELTA

    return {
        "id": device_id,
        "deviceId": device_id,
        "ts": ts_iso,
        "temp": row.temperature,
        "hum": row.humidity,
        "temperature": row.temperature,
        "humidity": row.humidity,
        "online": is_online,
    }


@app.get("/metrics")
def metrics(
    deviceId: Optional[str] = None,
    limit: int = 300,
    db: Session = Depends(get_db),
):
    device_id = _resolve_device(deviceId)
    limit = max(1, min(limit, 1000))

    rows = (
        db.execute(
            select(Telemetry)
            .where(Telemetry.device_id == device_id)
            .order_by(desc(Telemetry.ts))
            .limit(limit)
        )
        .scalars()
        .all()
    )

    return [
        {"ts": _to_iso(row.ts), "temp": row.temperature, "hum": row.humidity}
        for row in reversed(rows)
    ]


@app.get("/status")
def status(deviceId: Optional[str] = None, db: Session = Depends(get_db)):
    device_id = _resolve_device(deviceId)
    row = (
        db.execute(
            select(Telemetry.ts)
            .where(Telemetry.device_id == device_id)
            .order_by(desc(Telemetry.ts))
            .limit(1)
        )
        .scalar_one_or_none()
    )

    if row is None:
        return {"id": device_id, "online": False, "updatedAt": None}

    ts_iso = _to_iso(row)
    now = datetime.now(tz=timezone.utc)
    is_online = now - datetime.fromtimestamp(row, tz=timezone.utc) <= ONLINE_DELTA
    return {"id": device_id, "online": is_online, "updatedAt": ts_iso}


@app.get("/errors")
def errors(
    deviceId: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 200))
    stmt = select(IngestError).order_by(desc(IngestError.ts)).limit(limit)
    if deviceId:
        stmt = stmt.where(IngestError.device_id == deviceId)

    rows = db.execute(stmt).scalars().all()
    return [
        {
            "id": str(row.id),
            "deviceId": row.device_id,
            "ts": _to_iso(row.ts),
            "msg": row.reason,
        }
        for row in rows
    ]


@app.get("/metrics/prometheus")
def metrics_prometheus(db: Session = Depends(get_db)):
    total = db.execute(select(func.count()).select_from(Telemetry)).scalar_one()
    return f"ingest_ok_total {total}\n"
