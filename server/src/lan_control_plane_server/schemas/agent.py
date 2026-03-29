from datetime import datetime

from pydantic import BaseModel


class AgentRead(BaseModel):
    id: str
    host_id: str
    host_name: str
    version: str
    enabled: bool
    last_seen_at: datetime | None
