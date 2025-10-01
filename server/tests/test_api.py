from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ingest_and_latest():
    r = client.post(
        "/ingest",
        json={"deviceId": "esp32-01", "ts": 1, "temperature": 1.0, "humidity": 2.0},
    )
    assert (r.status_code == 200) and (r.json()["ok"] is True)

    r = client.get("/latest", params={"deviceId": "esp32-01"})
    js = r.json()
    assert (js["temperature"] == 1.0) and (js["humidity"] == 2.0) and "ts" in js
