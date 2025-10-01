from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://dev:devpw@127.0.0.1:5432/iot"
    MQTT_BROKER: str = "127.0.0.1"

    class Config:
        env_file = ".env"


settings = Settings()
