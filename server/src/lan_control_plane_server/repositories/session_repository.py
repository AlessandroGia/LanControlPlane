from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from lan_control_plane_server.db.models import Session as UserSession


class SessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        user_id: str,
        session_token_hash: str,
        expires_at: datetime,
    ) -> UserSession:
        db_session = UserSession(
            user_id=user_id,
            session_token_hash=session_token_hash,
            expires_at=expires_at,
        )
        self.session.add(db_session)
        self.session.commit()
        self.session.refresh(db_session)
        return db_session

    def get_valid_by_token_hash(self, token_hash: str) -> UserSession | None:
        now = datetime.now(UTC)
        statement = select(UserSession).where(
            UserSession.session_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
        return self.session.scalar(statement)

    def touch(self, db_session: UserSession) -> UserSession:
        db_session.last_seen_at = datetime.now(UTC)
        self.session.add(db_session)
        self.session.commit()
        self.session.refresh(db_session)
        return db_session

    def revoke(self, db_session: UserSession) -> UserSession:
        db_session.revoked_at = datetime.now(UTC)
        self.session.add(db_session)
        self.session.commit()
        self.session.refresh(db_session)
        return db_session
