from .helpers import create_host

API_KEY_HEADER = {"X-API-Key": "dev-rest-api-key"}


def test_patch_host_network_rejects_invalid_ip(client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")

    response = client.patch(
        "/hosts/desktop-casa/network",
        headers=API_KEY_HEADER,
        json={
            "ip_address": "not-an-ip",
            "mac_address": "AA:BB:CC:DD:EE:FF",
        },
    )

    assert response.status_code == 422


def test_patch_host_network_normalizes_mac(client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")

    response = client.patch(
        "/hosts/desktop-casa/network",
        headers=API_KEY_HEADER,
        json={
            "ip_address": "192.168.1.20",
            "mac_address": "aa-bb-cc-dd-ee-ff",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["mac_address"] == "AA:BB:CC:DD:EE:FF"


def test_get_hosts_returns_hosts(client, db_session):
    create_host(db_session, name="desktop-casa", hostname="desktop-casa", state="online")

    response = client.get("/hosts", headers=API_KEY_HEADER)

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["name"] == "desktop-casa"
    assert payload[0]["state"] == "online"


def test_get_host_returns_single_host(client, db_session):
    create_host(
        db_session,
        name="desktop-casa",
        hostname="desktop-casa",
        state="online",
        ip_address="192.168.1.20",
        mac_address="AA:BB:CC:DD:EE:FF",
    )

    response = client.get("/hosts/desktop-casa", headers=API_KEY_HEADER)

    assert response.status_code == 200
    payload = response.json()

    assert payload["name"] == "desktop-casa"
    assert payload["ip_address"] == "192.168.1.20"
    assert payload["mac_address"] == "AA:BB:CC:DD:EE:FF"


def test_patch_host_network_updates_values(client, db_session):
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
    payload = response.json()

    assert payload["ip_address"] == "192.168.1.20"
    assert payload["mac_address"] == "AA:BB:CC:DD:EE:FF"
