import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from lan_control_plane_shared.protocol.agent_messages import AgentHello
from lan_control_plane_shared.protocol.server_messages import Connected, ErrorMessage
from pydantic import ValidationError

from lan_control_plane_server.ws.agent_handler import (
    handle_agent_disconnect,
    handle_agent_message,
    register_agent_connection,
)
from lan_control_plane_server.ws.manager import manager

LOGGER = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/agent")
async def agent_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json(Connected(channel="agent").model_dump(mode="json"))

    agent_id: str | None = None
    try:
        raw_message = await websocket.receive_json()
        try:
            hello = AgentHello.model_validate(raw_message)
        except ValidationError:
            await websocket.send_json(ErrorMessage(message="Invalid hello message").model_dump(mode="json"))
            await websocket.close(code=1008)
            return

        agent_id = hello.agent_id
        if manager.has_agent(agent_id):
            await websocket.send_json(
                ErrorMessage(message="Another connection for this agent is already active").model_dump(mode="json")
            )
            await websocket.close(code=1008)
            return

        try:
            await register_agent_connection(websocket, hello)
        except (PermissionError, ValueError) as exc:
            await websocket.send_json(ErrorMessage(message=str(exc)).model_dump(mode="json"))
            await websocket.close(code=1008)
            return

        while True:
            raw_message = await websocket.receive_json()
            await handle_agent_message(websocket, agent_id, raw_message)
    except WebSocketDisconnect:
        pass
    except Exception:
        LOGGER.exception("Unexpected error in agent WebSocket for %s", agent_id or "unknown")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        if agent_id is not None:
            await handle_agent_disconnect(agent_id, websocket)
