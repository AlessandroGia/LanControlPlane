from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from lan_control_plane_server.services.auth_service import AuthService


def test_protected_endpoint_requires_session(client: TestClient) -> None:
    response = client.get("/hosts")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_login_me_and_logout(client: TestClient, db_session: Session) -> None:
    AuthService(db_session).create_user(username="admin", password="test-password", role="admin")

    login_response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "test-password"},
    )
    assert login_response.status_code == 200
    assert login_response.cookies.get("lcp_session")

    me_response = client.get("/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "admin"

    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_login_rejects_bad_password(client: TestClient, db_session: Session) -> None:
    AuthService(db_session).create_user(username="admin", password="test-password", role="admin")
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert response.status_code == 401
