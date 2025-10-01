from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from .db import get_db
from .models import Device, Telemetry

app = FastAPI()


class TelemetryIn(BaseModel):
    deviceId: str
    ts: int
    temperature: float
    humidity: float


@app.post("/ingest")
def ingest(t: TelemetryIn, db: Session = Depends(get_db)):
    # 確保 device 存在（若無則建立）
    dev = db.execute(
        select(Device).where(Device.device_id == t.deviceId)
    ).scalar_one_or_none()
    if not dev:
        dev = Device(device_id=t.deviceId)
        db.add(dev)
    # 寫入 telemetry
    db.add(
        Telemetry(
            device_id=t.deviceId,
            ts=t.ts,
            temperature=t.temperature,
            humidity=t.humidity,
        )
    )
    db.commit()
    return {"ok": True}


@app.get("/latest")
def latest(deviceId: str, db: Session = Depends(get_db)):
    row = db.execute(
        select(Telemetry)
        .where(Telemetry.device_id == deviceId)
        .order_by(desc(Telemetry.ts))
        .limit(1)
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="no data")
    return {
        "deviceId": row.device_id,
        "temperature": row.temperature,
        "humidity": row.humidity,
        "ts": row.ts,
    }


@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    total = db.execute(
        select(Telemetry).count()
    ).scalar()  # SQLAlchemy 2.x: select(func.count()).scalar_one()
    return f"ingest_ok_total {total}\n"
