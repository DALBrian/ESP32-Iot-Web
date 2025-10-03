from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://dev:devpw@127.0.0.1:5432/iot"
    MQTT_BROKER: str = "127.0.0.1"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "Test"
    MQTT_USERNAME: str | None = None
    MQTT_PASSWORD: str | None = None
    MQTT_ENABLED: bool = True
    DEFAULT_DEVICE_ID: str = "esp32-01"
    ONLINE_GRACE_SECONDS: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
