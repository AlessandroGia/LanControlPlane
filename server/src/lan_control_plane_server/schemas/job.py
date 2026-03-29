from datetime import datetime

from lan_control_plane_shared.enums.job_status import JobStatus
from pydantic import BaseModel


class JobRead(BaseModel):
    id: str
    host_id: str
    command: str
    status: JobStatus
    requested_by: str
    requested_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    result_message: str | None
