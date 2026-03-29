from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from lan_control_plane_server.db.base import Base
from lan_control_plane_server.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite://"


engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr("lan_control_plane_server.db.session.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("lan_control_plane_server.api.hosts.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("lan_control_plane_server.api.jobs.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("lan_control_plane_server.api.agents.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("lan_control_plane_server.api.audit_logs.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("lan_control_plane_server.ws.client_handler.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("lan_control_plane_server.ws.agent_handler.SessionLocal", TestingSessionLocal)

    with TestClient(app) as test_client:
        yield test_client
