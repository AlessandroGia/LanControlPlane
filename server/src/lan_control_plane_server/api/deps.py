from fastapi import Cookie, Header, HTTPException, status
from sqlalchemy.orm import Session

from lan_control_plane_server.core.config import get_settings
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.services.auth_service import AuthService


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()

    if x_api_key != settings.rest_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


def get_current_user_from_session(
    lcp_session: str | None = Cookie(default=None),
):
    if lcp_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    session: Session = SessionLocal()
    try:
        auth_service = AuthService(session)
        user = auth_service.get_user_from_session_token(lcp_session)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session",
            )
        return user
    finally:
        session.close()
