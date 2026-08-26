from .helpers import create_host


def test_get_audit_logs_returns_authenticated_actor(authenticated_client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")

    response = authenticated_client.patch(
        "/hosts/desktop-casa/network",
        json={
            "ip_address": "192.168.1.20",
            "mac_address": "AA:BB:CC:DD:EE:FF",
        },
    )
    assert response.status_code == 200

    response = authenticated_client.get("/audit-logs")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["actor_type"] == "user"
    assert payload[0]["actor_id"] == "admin"
    assert payload[0]["action"] == "host_network_updated"


def test_audit_logs_requires_session(client):
    response = client.get("/audit-logs")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_host_network_update_writes_normalized_metadata(authenticated_client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")
    response = authenticated_client.patch(
        "/hosts/desktop-casa/network",
        json={
            "ip_address": "192.168.1.20",
            "mac_address": "AA-BB-CC-DD-EE-FF",
        },
    )
    assert response.status_code == 200

    payload = authenticated_client.get("/audit-logs").json()
    metadata_json = payload[0]["metadata_json"]
    assert metadata_json is not None
    assert "192.168.1.20" in metadata_json
    assert "AA:BB:CC:DD:EE:FF" in metadata_json
