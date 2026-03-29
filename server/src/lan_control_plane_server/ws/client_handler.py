from fastapi import WebSocket
from pydantic import ValidationError

from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.services.audit_service import AuditService
from lan_control_plane_server.services.host_service import HostService
from lan_control_plane_server.services.job_service import JobService
from lan_control_plane_server.services.wol_service import WakeOnLanService
from lan_control_plane_server.ws.manager import manager
from lan_control_plane_shared.enums.command import Command
from lan_control_plane_shared.enums.host_state import HostState
from lan_control_plane_shared.enums.job_status import JobStatus
from lan_control_plane_shared.protocol.client_messages import ClientCommandRequest, ClientGetHosts
from lan_control_plane_shared.protocol.server_messages import (
    AuthOk,
    ErrorMessage,
    HostsSnapshot,
    CommandMessage,
)

async def _send_hosts_snapshot(websocket: WebSocket) -> None:
    session = SessionLocal()
    try:
        host_service = HostService(session)
        snapshot = HostsSnapshot(hosts=host_service.get_hosts_snapshot())
        await websocket.send_json(snapshot.model_dump(mode="json"))
    finally:
        session.close()

async def register_client_connection(websocket: WebSocket, *, user_role: str) -> None:
    await manager.connect_client(websocket)
    await websocket.send_json(AuthOk(role=user_role).model_dump(mode="json"))
    await _send_hosts_snapshot(websocket)


async def handle_client_disconnect(websocket: WebSocket) -> None:
    manager.disconnect_client(websocket)


async def handle_client_message(
    websocket: WebSocket,
    raw_message: dict[str, object],
    *,
    requested_by: str,
) -> None:
    message_type = raw_message.get("type")

    if message_type == "get_hosts":
        await _handle_get_hosts(websocket, raw_message)
        return

    if message_type == "command_request":
        await _handle_command_request(websocket, raw_message, requested_by=requested_by)
        return

    await websocket.send_json(
        ErrorMessage(message=f"Unsupported message type: {message_type}").model_dump(mode="json")
    )


async def _handle_get_hosts(websocket: WebSocket, raw_message: dict[str, object]) -> None:
    try:
        ClientGetHosts.model_validate(raw_message)
    except ValidationError:
        await websocket.send_json(
            ErrorMessage(message="Invalid get_hosts message").model_dump(mode="json")
        )
        return

    await _send_hosts_snapshot(websocket)


async def _handle_command_request(
    websocket: WebSocket,
    raw_message: dict[str, object],
    *,
    requested_by: str,
) -> None:
    try:
        command_request = ClientCommandRequest.model_validate(raw_message)
    except ValidationError:
        await websocket.send_json(
            ErrorMessage(message="Invalid command_request message").model_dump(mode="json")
        )
        return

    if command_request.command not in {Command.SHUTDOWN, Command.REBOOT, Command.WAKE}:
        await websocket.send_json(
            ErrorMessage(message="Unsupported command").model_dump(mode="json")
        )
        return

    session = SessionLocal()
    try:
        host_service = HostService(session)
        job_service = JobService(session)
        audit_service = AuditService(session)

        host = host_service.get_host_by_name(command_request.host_id)
        if host is None:
            await websocket.send_json(
                ErrorMessage(message="Host not found").model_dump(mode="json")
            )
            return

        job = job_service.create_job(
            host_id=host.id,
            command=command_request.command.value,
            requested_by=requested_by,
        )

        audit_service.log_event(
            actor_type="user",
            actor_id=requested_by,
            action=f"command_requested:{command_request.command.value}",
            target_type="host",
            target_id=host.name,
            metadata={
                "job_id": job.id,
                "request_id": command_request.request_id,
            },
        )
    finally:
        session.close()

    await manager.broadcast_job_update(
        job_id=job.id,
        status=JobStatus.PENDING,
        host_id=host.name,
        command=command_request.command.value,
        message="Job created",
    )

    if command_request.command == Command.WAKE:
        await _handle_wake_command(
            host_name=host.name,
            host_db_id=host.id,
            mac_address=host.mac_address,
            job_id=job.id,
            command=command_request.command.value,
        )
        return

    await _handle_agent_command(
        host_name=host.name,
        job_id=job.id,
        command=command_request.command.value,
    )


async def _handle_agent_command(
    *,
    host_name: str,
    job_id: str,
    command: str,
) -> None:
    sent = await manager.send_command_to_agent(
        host_name,
        CommandMessage(
            job_id=job_id,
            command=command,
        ).model_dump(mode="json"),
    )

    if sent:
        return

    session = SessionLocal()
    try:
        job_service = JobService(session)
        audit_service = AuditService(session)

        job_service.mark_job_failed(job_id, "Agent is offline or not connected")
        audit_service.log_event(
            actor_type="system",
            actor_id="server",
            action="command_dispatch_failed",
            target_type="host",
            target_id=host_name,
            metadata={
                "job_id": job_id,
                "command": command,
                "reason": "agent_not_connected",
            },
        )
    finally:
        session.close()

    await manager.broadcast_job_update(
        job_id=job_id,
        status=JobStatus.FAILED,
        host_id=host_name,
        command=command,
        message="Agent is offline or not connected",
    )

async def _handle_wake_command(
    *,
    host_name: str,
    host_db_id: str,
    mac_address: str | None,
    job_id: str,
    command: str,
) -> None:
    if not mac_address:
        session = SessionLocal()
        try:
            job_service = JobService(session)
            audit_service = AuditService(session)

            job_service.mark_job_failed(job_id, "Host has no MAC address configured")
            audit_service.log_event(
                actor_type="system",
                actor_id="server",
                action="wake_failed",
                target_type="host",
                target_id=host_name,
                metadata={
                    "reason": "missing_mac",
                    "job_id": job_id,
                    "host_id": host_db_id,
                },
            )
        finally:
            session.close()

        await manager.broadcast_job_update(
            job_id=job_id,
            status=JobStatus.FAILED,
            host_id=host_name,
            command=command,
            message="Host has no MAC address configured",
        )
        return

    try:
        wol_service = WakeOnLanService()
        wol_service.send_magic_packet(mac_address)
    except Exception as exc:
        session = SessionLocal()
        try:
            job_service = JobService(session)
            audit_service = AuditService(session)

            job_service.mark_job_failed(job_id, f"WOL failed: {exc}")
            audit_service.log_event(
                actor_type="system",
                actor_id="server",
                action="wake_failed",
                target_type="host",
                target_id=host_name,
                metadata={
                    "reason": str(exc),
                    "job_id": job_id,
                    "host_id": host_db_id,
                },
            )
        finally:
            session.close()

        await manager.broadcast_job_update(
            job_id=job_id,
            status=JobStatus.FAILED,
            host_id=host_name,
            command=command,
            message=f"WOL failed: {exc}",
        )
        return

    session = SessionLocal()
    try:
        job_service = JobService(session)
        audit_service = AuditService(session)
        host_service = HostService(session)

        host_service.mark_host_waking(host_name)
        job_service.mark_job_completed(job_id, "Magic packet sent")
        audit_service.log_event(
            actor_type="system",
            actor_id="server",
            action="wake_sent",
            target_type="host",
            target_id=host_name,
            metadata={
                "job_id": job_id,
                "host_id": host_db_id,
            },
        )
    finally:
        session.close()

    await manager.broadcast_host_status(host_name, HostState.WAKING)
    await manager.broadcast_job_update(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        host_id=host_name,
        command=command,
        message="Magic packet sent",
    )
