def test_client_websocket_connects_and_authenticates(client):
    with client.websocket_connect("/ws/client") as websocket:
        first = websocket.receive_json()
        assert first["type"] == "connected"
        assert first["channel"] == "client"

        websocket.send_json({"type": "auth", "token": "dev-client-token"})

        auth_ok = websocket.receive_json()
        assert auth_ok["type"] == "auth_ok"
        assert auth_ok["role"] == "admin"

        snapshot = websocket.receive_json()
        assert snapshot["type"] == "hosts_snapshot"
        assert isinstance(snapshot["hosts"], list)


def test_agent_websocket_connects_and_authenticates(client):
    with client.websocket_connect("/ws/agent") as websocket:
        first = websocket.receive_json()
        assert first["type"] == "connected"
        assert first["channel"] == "agent"

        websocket.send_json(
            {
                "type": "hello",
                "agent_id": "desktop-casa",
                "token": "change-me-agent-token",
                "hostname": "desktop-casa",
                "version": "0.1.0",
            }
        )

        auth_ok = websocket.receive_json()
        assert auth_ok["type"] == "auth_ok"
        assert auth_ok["role"] == "agent"
