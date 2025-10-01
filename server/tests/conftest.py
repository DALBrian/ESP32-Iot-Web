import os
import time
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db import get_db
from alembic import command
from alembic.config import Config as AlembicConfig


@pytest.fixture(scope="session")
def test_db_url():
    base = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://dev:devpw@127.0.0.1:5432/iot"
    )
    test_db = f"iot_test{int(time.time())}"
    admin_engine = create_engine(
        base.rsplit("/", 1)[0] + "/postgres", isolation_level="AUTOCOMMIT"
    )
    with admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_db} WITH (FORCE);"))
        conn.execute(text(f"CREATE DATABASE {test_db};"))

    yield base.rsplit("/", 1)[0] + f"/{test_db}"

    with admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_db} WITH (FORCE);"))


@pytest.fixture()
def migrated_engine(test_db_url):
    alembic_cfg = AlembicConfig("alembic.ini")
    os.environ["DATABASE_URL"] = test_db_url
    command.upgrade(alembic_cfg, "head")
    engine = create_engine(test_db_url)
    yield engine
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
