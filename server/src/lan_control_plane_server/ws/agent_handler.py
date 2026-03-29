from fastapi import WebSocket
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.services.agent_service import AgentService
from lan_control_plane_server.services.audit_service import AuditService
from lan_control_plane_server.services.host_service import HostService
from lan_control_plane_server.services.job_service import JobService
from lan_control_plane_server.services.metric_service import HostMetricService
from lan_control_plane_server.ws.manager import manager
from lan_control_plane_shared.enums.host_state import HostState
from lan_control_plane_shared.enums.job_status import JobStatus
from lan_control_plane_shared.protocol.agent_messages import (
    AgentAck,
    AgentHeartbeat,
    AgentHello,
    AgentResult,
)
from lan_control_plane_shared.protocol.server_messages import AuthOk, ErrorMessage
from pydantic import ValidationError


async def register_agent_connection(websocket: WebSocket, hello: AgentHello) -> str:
    agent_id = hello.agent_id

    session = SessionLocal()
    try:
        host_service = HostService(session)
        agent_service = AgentService(session)
        audit_service = AuditService(session)

        host = host_service.ensure_managed_host(
            name=hello.agent_id,
            hostname=hello.hostname,
            ip_address=hello.ip_address,
        )

        if hello.ip_address is not None or hello.mac_address is not None:
            host_service.update_host_network_info(
                name=hello.agent_id,
                ip_address=hello.ip_address,
                mac_address=hello.mac_address,
            )

            audit_service.log_event(
                actor_type="agent",
                actor_id=hello.agent_id,
                action="host_network_reported",
                target_type="host",
                target_id=hello.agent_id,
                metadata={
                    "ip_address": hello.ip_address,
                    "mac_address": hello.mac_address,
                },
            )

        agent_service.register_or_update_agent(
            host=host,
            token=hello.token,
            version=hello.version,
        )

        audit_service.log_event(
            actor_type="agent",
            actor_id=hello.agent_id,
            action="agent_registered",
            target_type="host",
            target_id=hello.agent_id,
            metadata={"version": hello.version},
        )
    except PermissionError as exc:
        session.close()
        await websocket.send_json(ErrorMessage(message=str(exc)).model_dump(mode="json"))
        await websocket.close(code=1008)
        raise
    else:
        session.close()

    await manager.connect_agent(agent_id, websocket)
    await websocket.send_json(AuthOk(role="agent").model_dump(mode="json"))
    await manager.broadcast_host_status(agent_id, HostState.ONLINE)

    return agent_id


async def handle_agent_disconnect(agent_id: str) -> None:
    manager.disconnect_agent(agent_id)

    session = SessionLocal()
    try:
        host_service = HostService(session)
        host_service.mark_host_offline(agent_id)
    finally:
        session.close()

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
    raw_message: dict[str, object],
) -> None:
    message_type = raw_message.get("type")

    if message_type == "heartbeat":
        await _handle_heartbeat(websocket, raw_message)
        return

    if message_type == "ack":
        await _handle_ack(raw_message)
        return

    if message_type == "result":
        await _handle_result(raw_message)
        return

    await websocket.send_json(ErrorMessage(message=f"Unsupported message type: {message_type}").model_dump(mode="json"))


async def _handle_heartbeat(websocket: WebSocket, raw_message: dict[str, object]) -> None:
    try:
        heartbeat = AgentHeartbeat.model_validate(raw_message)
    except ValidationError:
        await websocket.send_json(ErrorMessage(message="Invalid heartbeat message").model_dump(mode="json"))
        return

    session = SessionLocal()
    try:
        host_service = HostService(session)
        agent_service = AgentService(session)
        metric_service = HostMetricService(session)

        host = host_service.get_host_by_name(heartbeat.agent_id)
        if host is not None:
            host_service.mark_host_online(host.name)
            agent_service.touch_agent_last_seen(host=host)
            metric_service.record_heartbeat_metrics(
                host_id=host.id,
                cpu_usage=heartbeat.metrics.cpu,
                memory_usage=heartbeat.metrics.memory,
                uptime_seconds=heartbeat.uptime,
            )
    finally:
        session.close()

    await websocket.send_json(
        {
            "type": "heartbeat_ack",
            "agent_id": heartbeat.agent_id,
        }
    )


async def _handle_ack(raw_message: dict[str, object]) -> None:
    ack = AgentAck.model_validate(raw_message)

    session = SessionLocal()
    try:
        job_service = JobService(session)
        host_service = HostService(session)
        audit_service = AuditService(session)

        job = job_service.mark_job_running(ack.job_id)
        if job is None:
            return

        host = host_service.get_host_by_id(job.host_id)
        if host is None:
            return

        audit_service.log_event(
            actor_type="agent",
            actor_id=host.name,
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
        host_id=host.name,
        command=job.command,
        message="Job acknowledged by agent",
    )


async def _handle_result(raw_message: dict[str, object]) -> None:
    result = AgentResult.model_validate(raw_message)

    session = SessionLocal()
    try:
        job_service = JobService(session)
        host_service = HostService(session)
        audit_service = AuditService(session)

        if result.status == "ok":
            job = job_service.mark_job_completed(result.job_id, result.message)
        else:
            job = job_service.mark_job_failed(result.job_id, result.message)

        if job is None:
            return

        host = host_service.get_host_by_id(job.host_id)
        if host is None:
            return

        audit_service.log_event(
            actor_type="agent",
            actor_id=host.name,
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
        host_id=host.name,
        command=job.command,
        message=result.message,
    )
