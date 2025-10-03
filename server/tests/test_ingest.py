from datetime import datetime, timedelta, timezone


def _iso_to_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_ingest_schema(client):
    resp = client.post(
        "/ingest",
        json={"deviceId": "esp32-01", "ts": 1, "temperature": 1, "humidity": 1},
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_latest_and_metrics(client):
    device_id = "esp32-test"
    base_ts = int(datetime.now(tz=timezone.utc).timestamp())
    for offset, temp in enumerate([22.2, 22.5, 22.7]):
        client.post(
            "/ingest",
            json={
                "deviceId": device_id,
                "ts": base_ts + offset,
                "temperature": temp,
                "humidity": 40 + offset,
            },
        )

    latest = client.get("/latest", params={"deviceId": device_id})
    assert latest.status_code == 200
    body = latest.json()
    assert body["id"] == device_id
    assert body["temp"] == 22.7 and body["hum"] == 42
    assert body["online"] is True
    assert _iso_to_dt(body["ts"]) <= datetime.now(tz=timezone.utc) + timedelta(seconds=5)

    metrics = client.get("/metrics", params={"deviceId": device_id}).json()
    assert [point["temp"] for point in metrics] == [22.2, 22.5, 22.7]
    assert metrics[-1]["ts"] == body["ts"]
