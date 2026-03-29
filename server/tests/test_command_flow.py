from lan_control_plane_server.db.models import Job


def test_command_request_creates_job(client, db_session):
    with client.websocket_connect("/ws/agent") as agent_ws:
        agent_ws.receive_json()
        agent_ws.send_json(
            {
                "type": "hello",
                "agent_id": "desktop-casa",
                "token": "change-me-agent-token",
                "hostname": "desktop-casa",
                "version": "0.1.0",
            }
        )
        agent_ws.receive_json()

        with client.websocket_connect("/ws/client") as client_ws:
            client_ws.receive_json()
            client_ws.send_json({"type": "auth", "token": "dev-client-token"})
            client_ws.receive_json()
            client_ws.receive_json()

            client_ws.send_json(
                {
                    "type": "command_request",
                    "request_id": "req-1",
                    "host_id": "desktop-casa",
                    "command": "shutdown",
                }
            )

            update = client_ws.receive_json()
            assert update["type"] == "job_update"
            assert update["status"] == "pending"
            assert update["host_id"] == "desktop-casa"

    jobs = db_session.query(Job).all()
    assert len(jobs) == 1
    assert jobs[0].command == "shutdown"
    assert jobs[0].status in {"pending", "running", "completed", "failed"}
