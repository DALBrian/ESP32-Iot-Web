from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, Float, ForeignKey, Index, Integer, String
from .db import Base


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), unique=True, nullable=False)
    model = Column(String(100), nullable=True)


class Telemetry(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(
        String(100), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False
    )
    ts = Column(BigInteger, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)

    __table_args__ = (
        Index("ix_telemetry_device_ts", "device_id", "ts", postgresql_using="btree"),
    )


class IngestError(Base):
    __tablename__ = "errors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(100), nullable=True)
    ts = Column(
        BigInteger,
        nullable=False,
        default=lambda: int(datetime.now(tz=timezone.utc).timestamp()),
    )
    reason = Column(String(500), nullable=False)
