from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from lan_control_plane_server.core.security import validate_agent_token
from lan_control_plane_server.ws.agent_handler import (
    handle_agent_disconnect,
    handle_agent_message,
    register_agent_connection,
)
from lan_control_plane_shared.protocol.agent_messages import AgentHello
from lan_control_plane_shared.protocol.server_messages import Connected, ErrorMessage
from pydantic import ValidationError

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

        if not validate_agent_token(hello.token):
            await websocket.send_json(ErrorMessage(message="Invalid agent token").model_dump(mode="json"))
            await websocket.close(code=1008)
            return

        agent_id = await register_agent_connection(websocket, hello)

        while True:
            raw_message = await websocket.receive_json()
            await handle_agent_message(websocket, agent_id, raw_message)

    except WebSocketDisconnect:
        if agent_id is not None:
            await handle_agent_disconnect(agent_id)
