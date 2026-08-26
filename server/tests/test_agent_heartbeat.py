from datetime import UTC, datetime, timedelta

from lan_control_plane_server.db.models import Host, HostMetric

TEST_AGENT_TOKEN = "test-agent-token-123456789"
TEST_AGENT_ENROLLMENT_TOKEN = "test-enrollment-token-123456789"


def _connect_agent(client, *, agent_id: str = "desktop-casa"):
    websocket = client.websocket_connect("/ws/agent")
    connection = websocket.__enter__()
    assert connection.receive_json()["type"] == "connected"
    connection.send_json(
        {
            "type": "hello",
            "agent_id": agent_id,
            "token": TEST_AGENT_TOKEN,
            "enrollment_token": TEST_AGENT_ENROLLMENT_TOKEN,
            "hostname": agent_id,
            "version": "0.1.0",
        }
    )
    assert connection.receive_json()["type"] == "auth_ok"
    return websocket, connection


def test_agent_heartbeat_creates_metric(client, db_session):
    context, websocket = _connect_agent(client)
    try:
        websocket.send_json(
            {
                "type": "heartbeat",
                "agent_id": "desktop-casa",
                "uptime": 12345,
                "metrics": {"cpu": 12.5, "memory": 42.0},
            }
        )
        ack = websocket.receive_json()
        assert ack == {"type": "heartbeat_ack", "agent_id": "desktop-casa"}
    finally:
        context.__exit__(None, None, None)

    metrics = db_session.query(HostMetric).all()
    assert len(metrics) == 1
    assert metrics[0].cpu_usage == 12.5
    assert metrics[0].memory_usage == 42.0
    assert metrics[0].uptime_seconds == 12345


def test_agent_cannot_report_heartbeat_for_another_identity(client, db_session):
    context, websocket = _connect_agent(client)
    try:
        websocket.send_json(
            {
                "type": "heartbeat",
                "agent_id": "other-host",
                "uptime": 10,
                "metrics": {"cpu": 1.0, "memory": 2.0},
            }
        )
        error = websocket.receive_json()
        assert error["type"] == "error"
        assert "identity" in error["message"]
    finally:
        context.__exit__(None, None, None)

    assert db_session.query(HostMetric).count() == 0


def test_heartbeat_prunes_expired_metrics(client, db_session):
    context, websocket = _connect_agent(client)
    try:
        host = db_session.query(Host).filter_by(name="desktop-casa").one()
        db_session.add(
            HostMetric(
                host_id=host.id,
                cpu_usage=1,
                memory_usage=2,
                uptime_seconds=3,
                collected_at=datetime.now(UTC) - timedelta(days=31),
            )
        )
        db_session.commit()

        websocket.send_json(
            {
                "type": "heartbeat",
                "agent_id": "desktop-casa",
                "uptime": 4,
                "metrics": {"cpu": 5, "memory": 6},
            }
        )
        assert websocket.receive_json()["type"] == "heartbeat_ack"
    finally:
        context.__exit__(None, None, None)

    metrics = db_session.query(HostMetric).all()
    assert len(metrics) == 1
    assert metrics[0].uptime_seconds == 4
