from lan_control_plane_server.db.models import Job

TEST_AGENT_ENROLLMENT_TOKEN = "test-enrollment-token-123456789"


def _register_agent(websocket, agent_id: str) -> None:
    assert websocket.receive_json()["type"] == "connected"
    websocket.send_json(
        {
            "type": "hello",
            "agent_id": agent_id,
            "token": f"credential-{agent_id}-123456789",
            "enrollment_token": TEST_AGENT_ENROLLMENT_TOKEN,
            "hostname": agent_id,
            "version": "0.1.0",
        }
    )
    assert websocket.receive_json()["type"] == "auth_ok"


def test_command_request_runs_through_ack_and_result(authenticated_client, db_session):
    with authenticated_client.websocket_connect("/ws/agent") as agent_ws:
        _register_agent(agent_ws, "desktop-casa")

        with authenticated_client.websocket_connect(
            "/ws/client",
            headers={"origin": "http://testserver"},
        ) as client_ws:
            assert client_ws.receive_json()["type"] == "auth_ok"
            assert client_ws.receive_json()["type"] == "hosts_snapshot"

            client_ws.send_json(
                {
                    "type": "command_request",
                    "request_id": "req-command-0001",
                    "host_id": "desktop-casa",
                    "command": "reboot",
                }
            )
            pending = client_ws.receive_json()
            assert pending["type"] == "job_update"
            assert pending["status"] == "pending"

            command = agent_ws.receive_json()
            assert command["type"] == "command"
            agent_ws.send_json({"type": "ack", "job_id": command["job_id"]})
            assert client_ws.receive_json()["status"] == "running"

            agent_ws.send_json(
                {
                    "type": "result",
                    "job_id": command["job_id"],
                    "status": "ok",
                    "message": "reboot accepted",
                }
            )
            completed = client_ws.receive_json()
            assert completed["status"] == "completed"

    jobs = db_session.query(Job).all()
    assert len(jobs) == 1
    assert jobs[0].status == "completed"


def test_agent_cannot_ack_another_hosts_job(authenticated_client, db_session):
    with authenticated_client.websocket_connect("/ws/agent") as first_agent:
        _register_agent(first_agent, "desktop-one")
        with authenticated_client.websocket_connect("/ws/agent") as second_agent:
            _register_agent(second_agent, "desktop-two")
            with authenticated_client.websocket_connect(
                "/ws/client",
                headers={"origin": "http://testserver"},
            ) as client_ws:
                client_ws.receive_json()
                client_ws.receive_json()
                client_ws.send_json(
                    {
                        "type": "command_request",
                        "request_id": "req-command-0002",
                        "host_id": "desktop-one",
                        "command": "reboot",
                    }
                )
                pending = client_ws.receive_json()
                command = first_agent.receive_json()

                second_agent.send_json({"type": "ack", "job_id": command["job_id"]})
                error = second_agent.receive_json()
                assert error["type"] == "error"

                job = db_session.get(Job, pending["job_id"])
                assert job is not None
                db_session.refresh(job)
                assert job.status == "pending"
