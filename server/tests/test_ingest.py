def test_ingest_schema(client):
    r = client.post(
        "/ingest",
        json={"deviceId": "esp32-01", "ts": 1, "temperature": 1, "humidity": 1},
    )
    assert r.status_code == 200


def test_latest_ok(client):
    client.post(
        "/ingest",
        json={"deviceId": "esp32-02", "ts": 10, "temperature": 22.2, "humidity": 50},
    )
    r = client.get("/latest", params={"deviceId": "esp32-02"})
    assert r.status_code == 200
    body = r.json()
    assert body["deviceId"] == "esp32-02"
    assert "temperature" in body and "humidity" in body and "ts" in body
