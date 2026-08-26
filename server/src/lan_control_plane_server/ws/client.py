import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from lan_control_plane_shared.protocol.server_messages import ErrorMessage

from lan_control_plane_server.ws.auth import get_user_from_websocket_session, is_allowed_websocket_origin
from lan_control_plane_server.ws.client_handler import handle_client_message, register_client_connection
from lan_control_plane_server.ws.manager import manager

LOGGER = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/client")
async def client_ws(websocket: WebSocket) -> None:
    await websocket.accept()

    if not is_allowed_websocket_origin(websocket):
        await websocket.send_json(ErrorMessage(message="WebSocket origin is not allowed").model_dump(mode="json"))
        await websocket.close(code=1008)
        return

    user = await get_user_from_websocket_session(websocket)
    if user is None:
        await websocket.send_json(ErrorMessage(message="Not authenticated").model_dump(mode="json"))
        await websocket.close(code=1008)
        return

    register_client_connection(websocket)
    try:
        await websocket.send_json({"type": "auth_ok", "role": user.role})
        await handle_client_message(
            websocket,
            {"type": "get_hosts"},
            requested_by=user.username,
            user_role=user.role,
        )

        while True:
            raw_message = await websocket.receive_json()
            await handle_client_message(
                websocket,
                raw_message,
                requested_by=user.username,
                user_role=user.role,
            )
    except WebSocketDisconnect:
        pass
    except Exception:
        LOGGER.exception("Unexpected error in dashboard WebSocket for user %s", user.username)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        manager.disconnect_client(websocket)
