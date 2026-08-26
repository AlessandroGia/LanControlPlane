from fastapi import APIRouter, Cookie, HTTPException, Response, status

from lan_control_plane_server.api.deps import CurrentUser
from lan_control_plane_server.core.config import get_settings
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.schemas.auth import LoginRequest, UserMeRead
from lan_control_plane_server.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, response: Response) -> dict[str, str]:
    settings = get_settings()
    session = SessionLocal()
    try:
        auth_service = AuthService(session)
        user = auth_service.authenticate_user(
            username=payload.username,
            password=payload.password,
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        session_token = auth_service.create_session_for_user(user=user)
    finally:
        session.close()

    response.set_cookie(
        key="lcp_session",
        value=session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(
    response: Response,
    current_user: CurrentUser,
    lcp_session: str | None = Cookie(default=None),
) -> dict[str, str]:
    del current_user

    if lcp_session:
        session = SessionLocal()
        try:
            auth_service = AuthService(session)
            auth_service.revoke_session_token(lcp_session)
        finally:
            session.close()

    settings = get_settings()
    response.delete_cookie(
        key="lcp_session",
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return {"status": "ok"}


@router.get("/me", response_model=UserMeRead)
def me(current_user: CurrentUser) -> UserMeRead:
    return UserMeRead(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
    )
