from fastapi import APIRouter, Depends, Query

from lan_control_plane_server.api.deps import get_current_user_from_session
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.schemas.audit import AuditLogRead
from lan_control_plane_server.services.audit_service import AuditService

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit-logs"],
    dependencies=[Depends(get_current_user_from_session)],
)


@router.get("", response_model=list[AuditLogRead])
def get_audit_logs(limit: int = Query(default=100, ge=1, le=500)) -> list[AuditLogRead]:
    session = SessionLocal()
    try:
        audit_service = AuditService(session)
        logs = audit_service.get_logs(limit=limit)
        return [
            AuditLogRead(
                id=log.id,
                actor_type=log.actor_type,
                actor_id=log.actor_id,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                metadata_json=log.metadata_json,
                created_at=log.created_at,
            )
            for log in logs
        ]
    finally:
        session.close()
