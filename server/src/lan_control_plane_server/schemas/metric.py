from datetime import datetime

from pydantic import BaseModel


class HostMetricRead(BaseModel):
    id: str
    host_id: str
    cpu_usage: float
    memory_usage: float
    uptime_seconds: int
    collected_at: datetime


class HostLatestMetricRead(BaseModel):
    host_id: str
    host_name: str
    cpu_usage: float
    memory_usage: float
    uptime_seconds: int
    collected_at: datetime
