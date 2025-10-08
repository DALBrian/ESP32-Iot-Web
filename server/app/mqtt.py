"""MQTT ingestion background service."""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any

import paho.mqtt.client as mqtt
from sqlalchemy.exc import SQLAlchemyError

from .db import SessionLocal
from .services import persist_telemetry, record_ingest_error
from .settings import settings

logger = logging.getLogger(__name__)


def _parse_timestamp(value: Any) -> int:
    """Convert multiple timestamp formats into epoch seconds."""

    if value is None:
        return int(datetime.now(tz=timezone.utc).timestamp())

    if isinstance(value, (int, float)):
        # Accept milliseconds inputs as well
        if value > 1_000_000_000_000:
            return int(value / 1000)
        return int(value)

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return int(datetime.now(tz=timezone.utc).timestamp())
        # Numeric string
        if value.isdigit():
            return int(value)
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:  # pragma: no cover - fallback branch
            raise ValueError(f"invalid timestamp format: {value}") from exc
        return int(dt.timestamp())

    raise ValueError(f"unsupported timestamp type: {type(value)!r}")


class MQTTIngestService:
    """Subscribe to MQTT messages and persist telemetry readings."""

    def __init__(
        self,
        *,
        broker: str,
        port: int,
        topic: str,
        default_device_id: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._broker = broker
        self._port = port
        self._topic = topic
        self._default_device_id = default_device_id
        self._username = username
        self._password = password
        self._client: mqtt.Client | None = None
        self._lock = threading.Lock()
        self._running = False

    def start(self) -> None:
        if not settings.MQTT_ENABLED:
            logger.info("MQTT ingestion disabled via settings")
            return

        if not self._broker:
            logger.warning("No MQTT broker configured; ingestion skipped")
            return

        with self._lock:
            if self._running:
                return

            client = mqtt.Client()
            client.enable_logger(logger)
            client.on_connect = self._on_connect
            client.on_message = self._on_message
            client.on_disconnect = self._on_disconnect
            client.reconnect_delay_set(min_delay=1, max_delay=60)

            if self._username:
                client.username_pw_set(self._username, self._password)

            try:
                client.connect_async(self._broker, self._port)
            except OSError as exc:
                logger.error("MQTT connect failed: %s", exc)
            else:
                client.loop_start()
                self._client = client
                self._running = True
                logger.info(
                    "MQTT ingest connecting to %s:%s topic=%s",
                    self._broker,
                    self._port,
                    self._topic,
                )

    def stop(self) -> None:
        with self._lock:
            self._running = False
            if self._client is None:
                return
            try:
                self._client.disconnect()
                self._client.loop_stop()
            finally:
                self._client = None

    # MQTT callbacks -----------------------------------------------------
    def _on_connect(self, client: mqtt.Client, _userdata, _flags, reason_code, *_args):
        if reason_code != 0:
            logger.error("MQTT connection refused rc=%s", reason_code)
            return
        logger.info("MQTT connected, subscribing to %s", self._topic)
        client.subscribe(self._topic)

    def _on_disconnect(self, _client: mqtt.Client, _userdata, rc):
        if rc != 0:
            logger.warning("MQTT unexpected disconnect rc=%s", rc)
        else:
            logger.info("MQTT disconnected")

    def _on_message(self, _client: mqtt.Client, _userdata, message: mqtt.MQTTMessage):
        raw = message.payload
        try:
            payload = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as e:
            logger.error("[MQTT] UTF-8 decode error: %s; HEX=%s", e, raw.hex())
            self._persist_error("non-utf8 payload", None)
            return

        logger.warning("[MQTT] topic=%s payload=%s", message.topic, payload)

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            logger.error("[MQTT] JSON decode error: %s; HEX=%s", e, raw.hex())
            self._persist_error("invalid JSON payload", None)
            return
        device_id = data.get("deviceId") or data.get("device_id")
        if not isinstance(device_id, str) or not device_id:
            self._persist_error("missing or invalid deviceId", None)
            return

        try:
            ts = _parse_timestamp(data.get("ts"))
            temperature = float(data.get("temperature"))
            humidity = float(data.get("humidity"))
        except (TypeError, ValueError) as exc:
            self._persist_error(str(exc), device_id)
            return

        with SessionLocal() as db:
            try:
                persist_telemetry(
                    db,
                    device_id=device_id,
                    ts=ts,
                    temperature=temperature,
                    humidity=humidity,
                )
            except SQLAlchemyError as exc:  # pragma: no cover - defensive logging
                db.rollback()
                logger.exception("Failed to persist telemetry: %s", exc)
                record_ingest_error(
                    db, reason="database error during MQTT ingest", device_id=device_id
                )

    def _persist_error(self, reason: str, device_id: str | None) -> None:
        with SessionLocal() as db:
            record_ingest_error(db, reason=reason, device_id=device_id)
        logger.warning("MQTT ingest error for %s: %s", device_id or "<unknown>", reason)


mqtt_service = MQTTIngestService(
    broker=settings.MQTT_BROKER,
    port=settings.MQTT_PORT,
    topic=settings.MQTT_TOPIC,
    default_device_id=settings.DEFAULT_DEVICE_ID,
    username=settings.MQTT_USERNAME,
    password=settings.MQTT_PASSWORD,
)
