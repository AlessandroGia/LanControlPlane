from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from lan_control_plane_server.db.models import User
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.services.auth_service import AuthService


def get_current_user_from_session(
    lcp_session: str | None = Cookie(default=None),
) -> User:
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


CurrentUser = Annotated[User, Depends(get_current_user_from_session)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
