import asyncio

from fastapi import WebSocket

from lan_control_plane_server.core.config import get_settings
from lan_control_plane_server.db.models import User
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.services.auth_service import AuthService


def _get_user_for_session_token(session_token: str) -> User | None:
    session = SessionLocal()
    try:
        return AuthService(session).get_user_from_session_token(session_token)
    finally:
        session.close()


async def get_user_from_websocket_session(websocket: WebSocket) -> User | None:
    session_token = websocket.cookies.get("lcp_session")
    if not session_token:
        return None

    return await asyncio.to_thread(_get_user_for_session_token, session_token)


def is_allowed_websocket_origin(websocket: WebSocket) -> bool:
    origin = websocket.headers.get("origin")
    if origin is None:
        return True
    return origin in get_settings().cors_origins
