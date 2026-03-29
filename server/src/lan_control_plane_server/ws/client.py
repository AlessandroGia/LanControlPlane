from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from lan_control_plane_server.ws.auth import get_user_from_websocket_session
from lan_control_plane_server.ws.client_handler import (
    handle_client_disconnect,
    handle_client_message,
    register_client_connection,
)
from lan_control_plane_shared.protocol.server_messages import ErrorMessage

router = APIRouter()


@router.websocket("/ws/client")
async def client_ws(websocket: WebSocket) -> None:
    await websocket.accept()

    user = await get_user_from_websocket_session(websocket)
    if user is None:
        await websocket.send_json(
            ErrorMessage(message="Not authenticated").model_dump(mode="json")
        )
        await websocket.close(code=1008)
        return

    await register_client_connection(websocket, user_role=user.role)

    try:
        while True:
            raw_message = await websocket.receive_json()
            await handle_client_message(websocket, raw_message, requested_by=user.username)
    except WebSocketDisconnect:
        await handle_client_disconnect(websocket)
