from lan_control_plane_server.db.models import Agent, Host

from .helpers import create_host


def test_patch_host_network_rejects_invalid_ip(authenticated_client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")

    response = authenticated_client.patch(
        "/hosts/desktop-casa/network",
        json={
            "ip_address": "not-an-ip",
            "mac_address": "AA:BB:CC:DD:EE:FF",
        },
    )

    assert response.status_code == 422


def test_patch_host_network_normalizes_mac(authenticated_client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")

    response = authenticated_client.patch(
        "/hosts/desktop-casa/network",
        json={
            "ip_address": "192.168.1.20",
            "mac_address": "aa-bb-cc-dd-ee-ff",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["mac_address"] == "AA:BB:CC:DD:EE:FF"


def test_get_hosts_returns_hosts(authenticated_client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")

    response = authenticated_client.get("/hosts")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["name"] == "desktop-casa"
    assert payload[0]["state"] == "online"


def test_get_host_returns_single_host(authenticated_client, db_session):
    create_host(
        db_session,
        name="desktop-casa",
        hostname="desktop-casa",
        state="online",
        ip_address="192.168.1.20",
        mac_address="AA:BB:CC:DD:EE:FF",
    )

    response = authenticated_client.get("/hosts/desktop-casa")

    assert response.status_code == 200
    payload = response.json()

    assert payload["name"] == "desktop-casa"
    assert payload["ip_address"] == "192.168.1.20"
    assert payload["mac_address"] == "AA:BB:CC:DD:EE:FF"


def test_patch_host_network_updates_values(authenticated_client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")

    response = authenticated_client.patch(
        "/hosts/desktop-casa/network",
        json={
            "ip_address": "192.168.1.20",
            "mac_address": "AA:BB:CC:DD:EE:FF",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["ip_address"] == "192.168.1.20"
    assert payload["mac_address"] == "AA:BB:CC:DD:EE:FF"


def test_patch_host_network_preserves_omitted_field(authenticated_client, db_session):
    create_host(
        db_session,
        name="desktop-casa",
        hostname="desktop-casa",
        ip_address="192.168.1.20",
        mac_address="AA:BB:CC:DD:EE:FF",
    )

    response = authenticated_client.patch(
        "/hosts/desktop-casa/network",
        json={"ip_address": "192.168.1.21"},
    )
    assert response.status_code == 200
    assert response.json()["ip_address"] == "192.168.1.21"
    assert response.json()["mac_address"] == "AA:BB:CC:DD:EE:FF"


def test_patch_host_network_requires_admin(viewer_client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa")
    response = viewer_client.patch(
        "/hosts/desktop-casa/network",
        json={"ip_address": "192.168.1.21"},
    )
    assert response.status_code == 403


def test_delete_host_removes_stale_host_and_agent(authenticated_client, db_session):
    host = create_host(db_session, name="old-host", hostname="old-host", state="offline")
    db_session.add(
        Agent(
            host_id=host.id,
            token_hash="unused-test-token-hash",
            version="0.1.0",
            enabled=True,
        )
    )
    db_session.commit()

    response = authenticated_client.delete("/hosts/old-host")

    assert response.status_code == 204
    assert db_session.query(Host).filter_by(name="old-host").one_or_none() is None
    assert db_session.query(Agent).filter_by(host_id=host.id).one_or_none() is None


def test_delete_host_requires_admin(viewer_client, db_session):
    create_host(db_session, name="old-host", hostname="old-host", state="offline")

    response = viewer_client.delete("/hosts/old-host")

    assert response.status_code == 403


def test_delete_connected_host_is_rejected(authenticated_client, db_session, monkeypatch):
    create_host(db_session, name="online-host", hostname="online-host", state="online")
    monkeypatch.setattr(
        "lan_control_plane_server.api.hosts.manager.has_agent",
        lambda agent_id: agent_id == "online-host",
    )

    response = authenticated_client.delete("/hosts/online-host")

    assert response.status_code == 409
    assert db_session.query(Host).filter_by(name="online-host").one_or_none() is not None
