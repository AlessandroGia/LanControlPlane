import json

from lan_control_plane_server.db.models import AuditLog
from sqlalchemy import select
from sqlalchemy.orm import Session


class AuditLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        actor_type: str,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: str,
        metadata: dict[str, object] | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata_json=json.dumps(metadata) if metadata is not None else None,
        )
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def get_all(self, *, limit: int = 100) -> list[AuditLog]:
        statement = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        return list(self.session.scalars(statement).all())
