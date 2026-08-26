from lan_control_plane_server.db.models import Job

from .helpers import create_host


def test_wake_command_calls_authenticated_helper(
    authenticated_client,
    db_session,
    monkeypatch,
):
    create_host(
        db_session,
        name="desktop-casa",
        hostname="desktop-casa",
        state="offline",
        mac_address="AA:BB:CC:DD:EE:FF",
    )
    calls: list[str] = []

    async def fake_send_magic_packet(service, mac_address: str) -> None:
        assert service.helper_token == "test-wol-helper-token"
        calls.append(mac_address)

    monkeypatch.setattr(
        "lan_control_plane_server.services.wol_service.WakeOnLanService.send_magic_packet",
        fake_send_magic_packet,
    )

    with authenticated_client.websocket_connect(
        "/ws/client",
        headers={"origin": "http://testserver"},
    ) as websocket:
        websocket.receive_json()
        websocket.receive_json()
        websocket.send_json(
            {
                "type": "command_request",
                "request_id": "req-wake-0001",
                "host_id": "desktop-casa",
                "command": "wake",
            }
        )
        assert websocket.receive_json()["status"] == "pending"
        assert websocket.receive_json()["type"] == "host_status_changed"
        assert websocket.receive_json()["status"] == "completed"

    assert calls == ["AA:BB:CC:DD:EE:FF"]
    job = db_session.query(Job).one()
    db_session.refresh(job)
    assert job.status == "completed"
