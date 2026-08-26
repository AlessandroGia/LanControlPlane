from collections.abc import Generator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from lan_control_plane_server.db.base import Base
from lan_control_plane_server.main import app
from lan_control_plane_server.services.auth_service import AuthService
from lan_control_plane_server.ws.manager import manager

TEST_DATABASE_URL = "sqlite://"
TEST_AGENT_ENROLLMENT_TOKEN = "test-enrollment-token-123456789"

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
    manager.clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    manager.clear()
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
    modules_with_session = [
        "lan_control_plane_server.db.session",
        "lan_control_plane_server.api.auth",
        "lan_control_plane_server.api.deps",
        "lan_control_plane_server.api.hosts",
        "lan_control_plane_server.api.jobs",
        "lan_control_plane_server.api.agents",
        "lan_control_plane_server.api.audit_logs",
        "lan_control_plane_server.api.metrics",
        "lan_control_plane_server.main",
        "lan_control_plane_server.ws.auth",
        "lan_control_plane_server.ws.client_handler",
        "lan_control_plane_server.ws.agent_handler",
    ]
    for module in modules_with_session:
        monkeypatch.setattr(f"{module}.SessionLocal", TestingSessionLocal)

    settings = SimpleNamespace(
        access_token_expire_minutes=60,
        session_touch_interval_seconds=300,
        cookie_secure=False,
        agent_enrollment_token=TEST_AGENT_ENROLLMENT_TOKEN,
        agent_offline_after_seconds=60,
        metrics_retention_days=30,
        cors_origins=["http://testserver"],
        wol_helper_base_url="http://wol-helper:8099",
        wol_helper_token="test-wol-helper-token",
        wol_broadcast_ip="192.168.1.255",
        wol_port=9,
    )
    for target in [
        "lan_control_plane_server.api.auth.get_settings",
        "lan_control_plane_server.core.security.get_settings",
        "lan_control_plane_server.services.auth_service.get_settings",
        "lan_control_plane_server.services.agent_service.get_settings",
        "lan_control_plane_server.ws.auth.get_settings",
        "lan_control_plane_server.ws.client_handler.get_settings",
    ]:
        monkeypatch.setattr(target, lambda: settings)

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def authenticated_client(client: TestClient, db_session: Session) -> TestClient:
    AuthService(db_session).create_user(username="admin", password="test-password", role="admin")
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "test-password"},
    )
    assert response.status_code == 200
    return client


@pytest.fixture
def viewer_client(client: TestClient, db_session: Session) -> TestClient:
    AuthService(db_session).create_user(username="viewer", password="test-password", role="viewer")
    response = client.post(
        "/auth/login",
        json={"username": "viewer", "password": "test-password"},
    )
    assert response.status_code == 200
    return client
