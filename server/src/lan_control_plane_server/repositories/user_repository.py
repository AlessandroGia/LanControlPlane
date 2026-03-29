from sqlalchemy import select
from sqlalchemy.orm import Session

from lan_control_plane_server.db.models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return self.session.scalar(statement)

    def get_by_id(self, user_id: str) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.session.scalar(statement)

    def create(
        self,
        *,
        username: str,
        password_hash: str,
        role: str = "admin",
    ) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_password_and_role(self, user: User, *, password_hash: str, role: str) -> User:
        user.password_hash = password_hash
        user.role = role
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
