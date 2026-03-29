import asyncio
import json
import logging

import websockets
import socket

from lan_control_plane_agent.core.config import get_settings
from lan_control_plane_agent.core.logging import configure_logging
from lan_control_plane_agent.handlers.command_handler import handle_command
from lan_control_plane_agent.system.network_info import get_mac_address, get_primary_ip_address

LOGGER = logging.getLogger(__name__)


async def heartbeat_loop(
    websocket: websockets.ClientConnection,
    *,
    agent_id: str,
    interval: int,
) -> None:
    while True:
        heartbeat_message = {
            "type": "heartbeat",
            "agent_id": agent_id,
            "uptime": 12345,
            "metrics": {
                "cpu": 12.5,
                "memory": 42.0,
            },
        }
        await websocket.send(json.dumps(heartbeat_message))
        await asyncio.sleep(interval)


async def execute_remote_command(
    websocket: websockets.ClientConnection,
    *,
    job_id: str,
    command: str,
    dry_run: bool,
) -> None:
    ack_message = {
        "type": "ack",
        "job_id": job_id,
    }
    await websocket.send(json.dumps(ack_message))

    try:
        result_text = await handle_command(command=command, dry_run=dry_run)

        result_message = {
            "type": "result",
            "job_id": job_id,
            "status": "ok",
            "message": result_text,
        }
        await websocket.send(json.dumps(result_message))

    except Exception as exc:
        LOGGER.exception("Command execution failed: %s", exc)
        result_message = {
            "type": "result",
            "job_id": job_id,
            "status": "error",
            "message": str(exc),
        }
        await websocket.send(json.dumps(result_message))


async def receive_loop(
    websocket: websockets.ClientConnection,
    *,
    dry_run: bool,
) -> None:
    while True:
        message = await websocket.recv()
        LOGGER.info("Received: %s", message)

        payload = json.loads(message)
        message_type = payload.get("type")

        if message_type == "command":
            await execute_remote_command(
                websocket,
                job_id=payload["job_id"],
                command=payload["command"],
                dry_run=dry_run,
            )


async def run_agent() -> None:
    settings = get_settings()

    while True:
        try:
            LOGGER.info("Connecting to %s", settings.server_ws_agent_url)

            async with websockets.connect(settings.server_ws_agent_url) as websocket:
                hello_message = {
                    "type": "hello",
                    "agent_id": settings.agent_id,
                    "token": settings.agent_token,
                    "hostname": socket.gethostname(),
                    "version": "0.1.0",
                    "ip_address": get_primary_ip_address(),
                    "mac_address": get_mac_address(),
                }
                await websocket.send(json.dumps(hello_message))

                await asyncio.gather(
                    heartbeat_loop(
                        websocket,
                        agent_id=settings.agent_id,
                        interval=settings.ws_heartbeat_interval,
                    ),
                    receive_loop(
                        websocket,
                        dry_run=settings.dry_run,
                    ),
                )

        except Exception as exc:
            LOGGER.exception("Agent connection failed: %s", exc)
            await asyncio.sleep(5)


def main() -> None:
    configure_logging()
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()
