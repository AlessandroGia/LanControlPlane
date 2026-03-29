from fastapi import WebSocket

from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.services.auth_service import AuthService


async def get_user_from_websocket_session(websocket: WebSocket):
    session_token = websocket.cookies.get("lcp_session")
    if not session_token:
        return None

    session = SessionLocal()
    try:
        auth_service = AuthService(session)
        return auth_service.get_user_from_session_token(session_token)
    finally:
        session.close()
