# Test FastAPI-Postgres
Send `curl.exe -X POST "http://localhost:8000/ingest"  -H "Content-Type: application/json"  -d '{\"deviceId\":\"esp32-sim-1\",\"ts\":1727851200,\"temperature\":25.6,\"humidity\":60.1}'`

Data should add to Postgres and use below bash to monitor the data in the table `telemetry`

`docker compose exec postgres psql -U dev -d iot -c "SELECT id, device_id, ts, temperature, humidity FROM telemetry ORDER BY id DESC LIMIT 5;"`

# Test Mosquitto-Paho_MQTT-FastAPI
Use `test_mqtt_msg.json`. Otherwise the double quote in the MQTT msg will be replaced by Windows powershell.
```
cd server\tests
mosquitto_pub.exe -h localhost -p 1883 -t Test -q 1 -f .\test_mqtt_msg.json
```
Open mosquitto_sub in another terminal before publishing message to monitor publisher. `mosquitto_sub.exe -h localhost -p 1883 -t Test -v`
It should looks like this
```
> mosquitto_sub -h localhost -t Test -v
Test {"deviceId":"esp32-sim-1","ts":1727851200,"temperature":99.9,"humidity":12.3}
```
