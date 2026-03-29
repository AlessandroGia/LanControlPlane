from datetime import datetime

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: str
    actor_type: str
    actor_id: str
    action: str
    target_type: str
    target_id: str
    metadata_json: str | None
    created_at: datetime
