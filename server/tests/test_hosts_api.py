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
