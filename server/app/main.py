from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

app = FastAPI(title="IoT Ingest API")


class TelemetryIn(BaseModel):
    deviceId: str = Field(..., min_length=1)
    ts: Optional[int] = None
    temperature: float
    humidity: float


_latest: dict[str, TelemetryIn] = {}


@app.post("/ingest")
def ingest(t: TelemetryIn):
    if t.ts is None:
        t.ts = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    _latest[t.deviceId] = t
    return {"ok": True}


@app.get("/latest")
def latest(deviceId: str):
    t = _latest.get(deviceId)
    if not t:
        raise HTTPException(status_code=404, detail="device not found")
    return t


@app.get("/healthz")
def healthz():
    return {"ok", True}
