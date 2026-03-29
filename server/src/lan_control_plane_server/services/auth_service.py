from sqlalchemy.orm import Session

from lan_control_plane_server.core.security import (
    generate_session_token,
    get_session_expiry,
    hash_password,
    hash_session_token,
    verify_password,
)
from lan_control_plane_server.db.models import User
from lan_control_plane_server.repositories.session_repository import SessionRepository
from lan_control_plane_server.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, session: Session) -> None:
        self.user_repository = UserRepository(session)
        self.session_repository = SessionRepository(session)

    def create_user(self, *, username: str, password: str, role: str = "admin") -> User:
        return self.user_repository.create(
            username=username,
            password_hash=hash_password(password),
            role=role,
        )

    def authenticate_user(self, *, username: str, password: str) -> User | None:
        user = self.user_repository.get_by_username(username)
        if user is None:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    def create_session_for_user(self, *, user: User) -> str:
        raw_token = generate_session_token()
        self.session_repository.create(
            user_id=user.id,
            session_token_hash=hash_session_token(raw_token),
            expires_at=get_session_expiry(),
        )
        return raw_token

    def get_user_from_session_token(self, token: str) -> User | None:
        db_session = self.session_repository.get_valid_by_token_hash(hash_session_token(token))
        if db_session is None:
            return None

        self.session_repository.touch(db_session)
        return self.user_repository.get_by_id(db_session.user_id)

    def revoke_session_token(self, token: str) -> None:
        db_session = self.session_repository.get_valid_by_token_hash(hash_session_token(token))
        if db_session is None:
            return

        self.session_repository.revoke(db_session)
