from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.services import record_ingest_error


def test_status_endpoint_handles_missing_device(client):
    resp = client.get("/status", params={"deviceId": "unknown"})
    assert resp.status_code == 200
    assert resp.json() == {"id": "unknown", "online": False, "updatedAt": None}


def test_errors_endpoint_returns_recent_entries(client, db_session):
    now = int(datetime.now(tz=timezone.utc).timestamp())
    older = record_ingest_error(
        db_session,
        reason="wifi reconnect",
        device_id="esp32-err",
    )
    db_session.execute(
        text("UPDATE errors SET ts=:ts WHERE id=:id"),
        {"ts": now - 600, "id": older.id},
    )
    db_session.commit()

    record_ingest_error(
        db_session,
        reason="sensor timeout",
        device_id="esp32-err",
    )

    resp = client.get("/errors", params={"deviceId": "esp32-err"})
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["msg"] == "sensor timeout"
    assert body[0]["id"]
    assert body[0]["ts"].endswith("Z")


def test_status_becomes_offline_when_stale(client):
    device_id = "esp32-offline"
    stale_ts = int((datetime.now(tz=timezone.utc) - timedelta(minutes=10)).timestamp())
    client.post(
        "/ingest",
        json={
            "deviceId": device_id,
            "ts": stale_ts,
            "temperature": 10,
            "humidity": 50,
        },
    )

    resp = client.get("/status", params={"deviceId": device_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["online"] is False
    assert data["updatedAt"].endswith("Z")
