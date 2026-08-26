import pytest
from pydantic import ValidationError

from lan_control_plane_shared.protocol.agent_messages import AgentHeartbeat, AgentResult
from lan_control_plane_shared.protocol.client_messages import ClientCommandRequest


def test_heartbeat_rejects_out_of_range_metrics() -> None:
    with pytest.raises(ValidationError):
        AgentHeartbeat.model_validate(
            {
                "type": "heartbeat",
                "agent_id": "desktop-casa",
                "uptime": 10,
                "metrics": {"cpu": 101, "memory": 20},
            }
        )


def test_result_status_is_constrained() -> None:
    with pytest.raises(ValidationError):
        AgentResult.model_validate(
            {
                "type": "result",
                "job_id": "00000000-0000-0000-0000-000000000000",
                "status": "maybe",
                "message": "done",
            }
        )


def test_client_command_rejects_unsafe_host_identifier() -> None:
    with pytest.raises(ValidationError):
        ClientCommandRequest.model_validate(
            {
                "type": "command_request",
                "request_id": "request-0001",
                "host_id": "../../other-host",
                "command": "shutdown",
            }
        )
