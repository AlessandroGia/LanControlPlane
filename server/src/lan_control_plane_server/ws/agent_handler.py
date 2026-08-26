from fastapi import WebSocket
from lan_control_plane_shared.enums.host_state import HostState
from lan_control_plane_shared.enums.job_status import JobStatus
from lan_control_plane_shared.protocol.agent_messages import AgentAck, AgentHeartbeat, AgentHello, AgentResult
from lan_control_plane_shared.protocol.server_messages import AuthOk, ErrorMessage
from pydantic import ValidationError

from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.services.agent_service import AgentService
from lan_control_plane_server.services.audit_service import AuditService
from lan_control_plane_server.services.host_service import HostService
from lan_control_plane_server.services.job_service import JobService
from lan_control_plane_server.services.metric_service import HostMetricService
from lan_control_plane_server.utils.network import normalize_mac_address
from lan_control_plane_server.ws.manager import manager


async def _send_error(websocket: WebSocket, message: str) -> None:
    await websocket.send_json(ErrorMessage(message=message).model_dump(mode="json"))


async def register_agent_connection(websocket: WebSocket, hello: AgentHello) -> str:
    agent_id = hello.agent_id
    ip_address = str(hello.ip_address) if hello.ip_address is not None else None
    normalized_mac_address = normalize_mac_address(hello.mac_address)

    session = SessionLocal()
    try:
        host_service = HostService(session)
        agent_service = AgentService(session)
        audit_service = AuditService(session)

        # Authorization must happen before host state or network data is mutated.
        agent_service.authorize_connection(
            host_name=agent_id,
            token=hello.token,
            enrollment_token=hello.enrollment_token,
        )

        host = host_service.ensure_managed_host(
            name=agent_id,
            hostname=hello.hostname,
            ip_address=ip_address,
        )

        if ip_address is not None or normalized_mac_address is not None:
            updated_host = host_service.update_host_network_info(
                name=agent_id,
                ip_address=ip_address if ip_address is not None else host.ip_address,
                mac_address=(normalized_mac_address if normalized_mac_address is not None else host.mac_address),
            )
            if updated_host is None:
                raise RuntimeError("Registered host disappeared during agent setup")
            host = updated_host

            audit_service.log_event(
                actor_type="agent",
                actor_id=agent_id,
                action="host_network_reported",
                target_type="host",
                target_id=agent_id,
                metadata={
                    "ip_address": ip_address,
                    "mac_address": normalized_mac_address,
                },
            )

        agent_service.register_or_update_agent(
            host=host,
            token=hello.token,
            version=hello.version,
        )

        audit_service.log_event(
            actor_type="agent",
            actor_id=agent_id,
            action="agent_registered",
            target_type="host",
            target_id=agent_id,
            metadata={"version": hello.version},
        )
    finally:
        session.close()

    if not manager.connect_agent(agent_id, websocket):
        raise PermissionError("Another connection for this agent is already active")

    await websocket.send_json(AuthOk(role="agent").model_dump(mode="json"))
    await manager.broadcast_host_status(agent_id, HostState.ONLINE)
    return agent_id


async def handle_agent_disconnect(agent_id: str, websocket: WebSocket) -> None:
    if not manager.disconnect_agent(agent_id, websocket):
        return

    session = SessionLocal()
    try:
        host_service = HostService(session)
        audit_service = AuditService(session)
        host_service.mark_host_offline(agent_id)
        audit_service.log_event(
            actor_type="agent",
            actor_id=agent_id,
            action="agent_disconnected",
            target_type="host",
            target_id=agent_id,
        )
    finally:
        session.close()

    await manager.broadcast_host_status(agent_id, HostState.OFFLINE)


async def handle_agent_message(
    websocket: WebSocket,
    agent_id: str,
    raw_message: object,
) -> None:
    if not manager.is_agent_connection(agent_id, websocket):
        await _send_error(websocket, "Agent connection is no longer active")
        return
    manager.touch_agent(agent_id, websocket)

    if not isinstance(raw_message, dict):
        await _send_error(websocket, "Message must be a JSON object")
        return

    message_type = raw_message.get("type")
    if message_type == "heartbeat":
        await _handle_heartbeat(websocket, agent_id, raw_message)
    elif message_type == "ack":
        await _handle_ack(websocket, agent_id, raw_message)
    elif message_type == "result":
        await _handle_result(websocket, agent_id, raw_message)
    else:
        await _send_error(websocket, f"Unsupported message type: {message_type}")


async def _handle_heartbeat(
    websocket: WebSocket,
    agent_id: str,
    raw_message: dict[str, object],
) -> None:
    try:
        heartbeat = AgentHeartbeat.model_validate(raw_message)
    except ValidationError:
        await _send_error(websocket, "Invalid heartbeat message")
        return

    if heartbeat.agent_id != agent_id:
        await _send_error(websocket, "Heartbeat agent identity does not match the connection")
        return

    session = SessionLocal()
    try:
        host_service = HostService(session)
        agent_service = AgentService(session)
        metric_service = HostMetricService(session)

        host = host_service.get_host_by_name(agent_id)
        if host is None:
            await _send_error(websocket, "Registered host no longer exists")
            return

        agent_service.touch_agent_last_seen(host=host)
        metric_service.record_heartbeat_metrics(
            host_id=host.id,
            cpu_usage=heartbeat.metrics.cpu,
            memory_usage=heartbeat.metrics.memory,
            uptime_seconds=heartbeat.uptime,
        )
    finally:
        session.close()

    await manager.broadcast_agent_heartbeat(agent_id)
    await websocket.send_json({"type": "heartbeat_ack", "agent_id": agent_id})


async def _handle_ack(
    websocket: WebSocket,
    agent_id: str,
    raw_message: dict[str, object],
) -> None:
    try:
        ack = AgentAck.model_validate(raw_message)
    except ValidationError:
        await _send_error(websocket, "Invalid acknowledgement message")
        return

    session = SessionLocal()
    try:
        job_service = JobService(session)
        host_service = HostService(session)
        audit_service = AuditService(session)

        host = host_service.get_host_by_name(agent_id)
        if host is None:
            await _send_error(websocket, "Registered host no longer exists")
            return

        job = job_service.mark_job_running(ack.job_id, expected_host_id=host.id)
        if job is None:
            await _send_error(websocket, "Job is unknown, belongs to another host, or is no longer pending")
            return

        audit_service.log_event(
            actor_type="agent",
            actor_id=agent_id,
            action="job_acknowledged",
            target_type="job",
            target_id=job.id,
            metadata={"command": job.command},
        )
    finally:
        session.close()

    await manager.broadcast_job_update(
        job_id=job.id,
        status=JobStatus.RUNNING,
        host_id=agent_id,
        command=job.command,
        message="Job acknowledged by agent",
    )


async def _handle_result(
    websocket: WebSocket,
    agent_id: str,
    raw_message: dict[str, object],
) -> None:
    try:
        result = AgentResult.model_validate(raw_message)
    except ValidationError:
        await _send_error(websocket, "Invalid result message")
        return

    session = SessionLocal()
    try:
        job_service = JobService(session)
        host_service = HostService(session)
        audit_service = AuditService(session)

        host = host_service.get_host_by_name(agent_id)
        if host is None:
            await _send_error(websocket, "Registered host no longer exists")
            return

        if result.status == "ok":
            job = job_service.mark_job_completed(
                result.job_id,
                result.message,
                expected_host_id=host.id,
            )
        else:
            job = job_service.mark_job_failed(
                result.job_id,
                result.message,
                expected_host_id=host.id,
            )

        if job is None:
            await _send_error(websocket, "Job is unknown, belongs to another host, or is already finished")
            return

        audit_service.log_event(
            actor_type="agent",
            actor_id=agent_id,
            action=f"job_{job.status}",
            target_type="job",
            target_id=job.id,
            metadata={"command": job.command, "message": result.message},
        )
    finally:
        session.close()

    await manager.broadcast_job_update(
        job_id=job.id,
        status=JobStatus(job.status),
        host_id=agent_id,
        command=job.command,
        message=result.message,
    )
