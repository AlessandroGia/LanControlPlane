from .helpers import create_host

API_KEY_HEADER = {"X-API-Key": "dev-rest-api-key"}


def test_get_audit_logs_returns_logs(client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")

    response = client.patch(
        "/hosts/desktop-casa/network",
        headers=API_KEY_HEADER,
        json={
            "ip_address": "192.168.1.20",
            "mac_address": "AA:BB:CC:DD:EE:FF",
        },
    )
    assert response.status_code == 200

    response = client.get("/audit-logs", headers=API_KEY_HEADER)

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["actor_type"] == "rest_api"
    assert payload[0]["actor_id"] == "admin"
    assert payload[0]["action"] == "host_network_updated"
    assert payload[0]["target_type"] == "host"
    assert payload[0]["target_id"] == "desktop-casa"


def test_audit_logs_requires_api_key(client):
    response = client.get("/audit-logs")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_host_network_update_writes_metadata_in_audit_log(client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")

    response = client.patch(
        "/hosts/desktop-casa/network",
        headers=API_KEY_HEADER,
        json={
            "ip_address": "192.168.1.20",
            "mac_address": "AA-BB-CC-DD-EE-FF",
        },
    )
    assert response.status_code == 200

    response = client.get("/audit-logs", headers=API_KEY_HEADER)
    assert response.status_code == 200

    payload = response.json()
    assert len(payload) == 1

    metadata_json = payload[0]["metadata_json"]
    assert metadata_json is not None
    assert "192.168.1.20" in metadata_json
    assert "AA:BB:CC:DD:EE:FF" in metadata_json
