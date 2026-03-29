from lan_control_plane_server.db.models import AuditLog
from lan_control_plane_server.repositories.audit_log_repository import AuditLogRepository
from sqlalchemy.orm import Session


class AuditService:
    def __init__(self, session: Session) -> None:
        self.audit_log_repository = AuditLogRepository(session)

    def log_event(
        self,
        *,
        actor_type: str,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: str,
        metadata: dict[str, object] | None = None,
    ) -> AuditLog:
        return self.audit_log_repository.create(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
        )

    def get_logs(self, *, limit: int = 100) -> list[AuditLog]:
        return self.audit_log_repository.get_all(limit=limit)
