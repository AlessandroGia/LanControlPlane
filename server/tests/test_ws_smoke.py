TEST_AGENT_TOKEN = "test-agent-token-123456789"
TEST_AGENT_ENROLLMENT_TOKEN = "test-enrollment-token-123456789"


def test_client_websocket_authenticates_from_session(authenticated_client):
    with authenticated_client.websocket_connect(
        "/ws/client",
        headers={"origin": "http://testserver"},
    ) as websocket:
        auth_ok = websocket.receive_json()
        assert auth_ok == {"type": "auth_ok", "role": "admin"}

        snapshot = websocket.receive_json()
        assert snapshot["type"] == "hosts_snapshot"
        assert isinstance(snapshot["hosts"], list)


def test_client_websocket_rejects_disallowed_origin(authenticated_client):
    with authenticated_client.websocket_connect(
        "/ws/client",
        headers={"origin": "https://evil.example"},
    ) as websocket:
        error = websocket.receive_json()
        assert error["type"] == "error"
        assert "origin" in error["message"].lower()


def test_viewer_websocket_cannot_send_commands(viewer_client, db_session):
    from .helpers import create_host

    create_host(db_session, name="desktop-casa", hostname="desktop-casa")
    with viewer_client.websocket_connect(
        "/ws/client",
        headers={"origin": "http://testserver"},
    ) as websocket:
        websocket.receive_json()
        websocket.receive_json()
        websocket.send_json(
            {
                "type": "command_request",
                "request_id": "viewer-request-01",
                "host_id": "desktop-casa",
                "command": "reboot",
            }
        )
        error = websocket.receive_json()
        assert error["type"] == "error"
        assert "administrator" in error["message"].lower()


def test_agent_websocket_connects_and_authenticates(client):
    with client.websocket_connect("/ws/agent") as websocket:
        assert websocket.receive_json()["type"] == "connected"
        websocket.send_json(
            {
                "type": "hello",
                "agent_id": "desktop-casa",
                "token": TEST_AGENT_TOKEN,
                "enrollment_token": TEST_AGENT_ENROLLMENT_TOKEN,
                "hostname": "desktop-casa",
                "version": "0.1.0",
            }
        )
        auth_ok = websocket.receive_json()
        assert auth_ok == {"type": "auth_ok", "role": "agent"}


def test_agent_credential_cannot_be_reused_for_another_host(client):
    with client.websocket_connect("/ws/agent") as first_websocket:
        first_websocket.receive_json()
        first_websocket.send_json(
            {
                "type": "hello",
                "agent_id": "desktop-one",
                "token": TEST_AGENT_TOKEN,
                "enrollment_token": TEST_AGENT_ENROLLMENT_TOKEN,
                "hostname": "desktop-one",
                "version": "0.1.0",
            }
        )
        assert first_websocket.receive_json()["type"] == "auth_ok"

    with client.websocket_connect("/ws/agent") as second_websocket:
        second_websocket.receive_json()
        second_websocket.send_json(
            {
                "type": "hello",
                "agent_id": "desktop-two",
                "token": TEST_AGENT_TOKEN,
                "enrollment_token": TEST_AGENT_ENROLLMENT_TOKEN,
                "hostname": "desktop-two",
                "version": "0.1.0",
            }
        )
        error = second_websocket.receive_json()
        assert error["type"] == "error"
        assert "another host" in error["message"]


def test_registered_agent_can_rotate_credential_with_enrollment_token(client):
    rotated_token = "rotated-agent-token-123456789"

    with client.websocket_connect("/ws/agent") as websocket:
        websocket.receive_json()
        websocket.send_json(
            {
                "type": "hello",
                "agent_id": "desktop-casa",
                "token": TEST_AGENT_TOKEN,
                "enrollment_token": TEST_AGENT_ENROLLMENT_TOKEN,
                "hostname": "desktop-casa",
                "version": "0.1.0",
            }
        )
        assert websocket.receive_json()["type"] == "auth_ok"

    with client.websocket_connect("/ws/agent") as websocket:
        websocket.receive_json()
        websocket.send_json(
            {
                "type": "hello",
                "agent_id": "desktop-casa",
                "token": rotated_token,
                "enrollment_token": TEST_AGENT_ENROLLMENT_TOKEN,
                "hostname": "desktop-casa",
                "version": "0.1.0",
            }
        )
        assert websocket.receive_json()["type"] == "auth_ok"

    with client.websocket_connect("/ws/agent") as websocket:
        websocket.receive_json()
        websocket.send_json(
            {
                "type": "hello",
                "agent_id": "desktop-casa",
                "token": TEST_AGENT_TOKEN,
                "hostname": "desktop-casa",
                "version": "0.1.0",
            }
        )
        assert websocket.receive_json()["type"] == "error"

    with client.websocket_connect("/ws/agent") as websocket:
        websocket.receive_json()
        websocket.send_json(
            {
                "type": "hello",
                "agent_id": "desktop-casa",
                "token": rotated_token,
                "hostname": "desktop-casa",
                "version": "0.1.0",
            }
        )
        assert websocket.receive_json()["type"] == "auth_ok"
