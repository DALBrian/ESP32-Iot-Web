import os
import sys
import time
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

os.environ.setdefault("MQTT_ENABLED", "0")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app
from app.db import Base, get_db
from alembic import command
from alembic.config import Config as AlembicConfig


def _sqlite_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def migrated_engine():
    base = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://dev:devpw@127.0.0.1:5432/iot"
    )
    if base.startswith("postgresql"):
        test_db = f"iot_test{int(time.time())}"
        admin_url = base.rsplit("/", 1)[0] + "/postgres"
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        try:
            with admin_engine.connect() as conn:
                conn.execute(text(f"DROP DATABASE IF EXISTS {test_db} WITH (FORCE);"))
                conn.execute(text(f"CREATE DATABASE {test_db};"))

            test_url = base.rsplit("/", 1)[0] + f"/{test_db}"
            alembic_cfg = AlembicConfig("alembic.ini")
            os.environ["DATABASE_URL"] = test_url
            command.upgrade(alembic_cfg, "head")
            engine = create_engine(test_url)
        except OperationalError:
            admin_engine.dispose()
            engine = _sqlite_engine()
        else:
            yield engine
            engine.dispose()
            with admin_engine.connect() as conn:
                conn.execute(text(f"DROP DATABASE IF EXISTS {test_db} WITH (FORCE);"))
            admin_engine.dispose()
            return
    else:
        engine = create_engine(base)
        try:
            yield engine
        finally:
            engine.dispose()
            return

    # fallback path (SQLite)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(migrated_engine):
    TestingSessionLocal = sessionmaker(
        bind=migrated_engine, autoflush=False, autocommit=False
    )
    sess = TestingSessionLocal()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture()
def client(db_session):
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
