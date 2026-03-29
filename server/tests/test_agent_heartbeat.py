from lan_control_plane_server.db.models import HostMetric


def test_agent_heartbeat_creates_metric(client, db_session):
    with client.websocket_connect("/ws/agent") as websocket:
        websocket.receive_json()

        websocket.send_json(
            {
                "type": "hello",
                "agent_id": "desktop-casa",
                "token": "change-me-agent-token",
                "hostname": "desktop-casa",
                "version": "0.1.0",
            }
        )

        websocket.receive_json()

        websocket.send_json(
            {
                "type": "heartbeat",
                "agent_id": "desktop-casa",
                "uptime": 12345,
                "metrics": {
                    "cpu": 12.5,
                    "memory": 42.0,
                },
            }
        )

        ack = websocket.receive_json()
        assert ack["type"] == "heartbeat_ack"
        assert ack["agent_id"] == "desktop-casa"

    metrics = db_session.query(HostMetric).all()
    assert len(metrics) == 1
    assert metrics[0].cpu_usage == 12.5
    assert metrics[0].memory_usage == 42.0
    assert metrics[0].uptime_seconds == 12345
