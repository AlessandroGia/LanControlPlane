from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from lan_control_plane_server.api.deps import get_current_user_from_session
from lan_control_plane_server.db.models import User
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.schemas.auth import LoginRequest, UserMeRead
from lan_control_plane_server.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(payload: LoginRequest, response: Response) -> dict[str, str]:
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
        secure=False,
        samesite="lax",
        path="/",
    )
    return {"status": "ok"}


@router.post("/logout")
async def logout(
    response: Response,
    lcp_session: str | None = Cookie(default=None),
    current_user: User = Depends(get_current_user_from_session),
) -> dict[str, str]:
    del current_user

    if lcp_session:
        session = SessionLocal()
        try:
            auth_service = AuthService(session)
            auth_service.revoke_session_token(lcp_session)
        finally:
            session.close()

    response.delete_cookie(key="lcp_session", path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserMeRead)
async def me(current_user: User = Depends(get_current_user_from_session)) -> UserMeRead:
    return UserMeRead(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
    )
