import asyncio
import contextlib
import json
import logging
import random
import socket

import websockets
from lan_control_plane_shared.protocol.server_messages import CommandMessage
from pydantic import ValidationError

from lan_control_plane_agent.core.config import get_settings
from lan_control_plane_agent.core.logging import configure_logging
from lan_control_plane_agent.handlers.command_handler import handle_command
from lan_control_plane_agent.system.metrics import get_cpu_usage, get_memory_usage, get_uptime_seconds
from lan_control_plane_agent.system.network_info import get_mac_address, get_primary_ip_address

LOGGER = logging.getLogger(__name__)


def normalize_mac_address(mac_address: str | None) -> str | None:
    if mac_address is None:
        return None
    return mac_address.strip().replace("-", ":").upper()


async def heartbeat_loop(
    websocket: websockets.ClientConnection,
    *,
    agent_id: str,
    interval: int,
) -> None:
    while True:
        await websocket.send(
            json.dumps(
                {
                    "type": "heartbeat",
                    "agent_id": agent_id,
                    "uptime": get_uptime_seconds(),
                    "metrics": {
                        "cpu": get_cpu_usage(),
                        "memory": get_memory_usage(),
                    },
                }
            )
        )
        await asyncio.sleep(interval)


async def execute_remote_command(
    websocket: websockets.ClientConnection,
    *,
    job_id: str,
    command: str,
    dry_run: bool,
) -> None:
    await websocket.send(json.dumps({"type": "ack", "job_id": job_id}))
    try:
        result_text = await handle_command(command=command, dry_run=dry_run)
        result_message = {
            "type": "result",
            "job_id": job_id,
            "status": "ok",
            "message": result_text,
        }
    except Exception as exc:
        LOGGER.exception("Command execution failed: %s", exc)
        result_message = {
            "type": "result",
            "job_id": job_id,
            "status": "error",
            "message": str(exc)[:4096],
        }
    await websocket.send(json.dumps(result_message))


async def receive_loop(
    websocket: websockets.ClientConnection,
    *,
    dry_run: bool,
) -> None:
    while True:
        message = await websocket.recv()
        try:
            payload = json.loads(message)
        except (json.JSONDecodeError, TypeError):
            LOGGER.warning("Ignoring a non-JSON server message")
            continue

        if not isinstance(payload, dict) or payload.get("type") != "command":
            continue

        try:
            command_message = CommandMessage.model_validate(payload)
        except ValidationError:
            LOGGER.warning("Ignoring an invalid command message")
            continue

        await execute_remote_command(
            websocket,
            job_id=command_message.job_id,
            command=command_message.command,
            dry_run=dry_run,
        )


async def _run_connected_agent() -> None:
    settings = get_settings()
    normalized_mac = normalize_mac_address(get_mac_address())

    async with websockets.connect(
        settings.server_ws_agent_url,
        open_timeout=10,
        ping_interval=20,
        ping_timeout=20,
        max_size=64 * 1024,
    ) as websocket:
        await websocket.send(
            json.dumps(
                {
                    "type": "hello",
                    "agent_id": settings.agent_id,
                    "token": settings.agent_token,
                    "enrollment_token": settings.agent_enrollment_token,
                    "hostname": socket.gethostname(),
                    "version": "0.1.0",
                    "ip_address": get_primary_ip_address(),
                    "mac_address": normalized_mac,
                }
            )
        )

        heartbeat_task = asyncio.create_task(
            heartbeat_loop(
                websocket,
                agent_id=settings.agent_id,
                interval=settings.ws_heartbeat_interval,
            )
        )
        try:
            await receive_loop(websocket, dry_run=settings.dry_run)
        finally:
            heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat_task


async def run_agent() -> None:
    settings = get_settings()
    retry_delay = 1.0
    while True:
        try:
            LOGGER.info("Connecting to %s", settings.server_ws_agent_url)
            await _run_connected_agent()
            retry_delay = 1.0
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            LOGGER.warning("Agent connection failed: %s", exc)
            jitter = random.uniform(0, min(1.0, retry_delay / 4))
            await asyncio.sleep(retry_delay + jitter)
            retry_delay = min(retry_delay * 2, 30.0)


def main() -> None:
    configure_logging()
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()
