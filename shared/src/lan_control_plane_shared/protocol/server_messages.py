from typing import Any

from lan_control_plane_shared.enums.host_state import HostState
from lan_control_plane_shared.enums.job_status import JobStatus
from lan_control_plane_shared.protocol.base import MessageBase
from pydantic import BaseModel, ConfigDict


class HostSnapshotItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    state: HostState
    is_managed: bool


class AuthOk(MessageBase):
    type: str = "auth_ok"
    role: str


class Connected(MessageBase):
    type: str = "connected"
    channel: str


class HostsSnapshot(MessageBase):
    type: str = "hosts_snapshot"
    hosts: list[HostSnapshotItem]


class HostStatusChanged(MessageBase):
    type: str = "host_status_changed"
    host_id: str
    state: HostState


class JobUpdate(MessageBase):
    type: str = "job_update"
    job_id: str
    status: JobStatus
    host_id: str
    command: str
    message: str | None = None


class ErrorMessage(MessageBase):
    type: str = "error"
    message: str


class EchoMessage(MessageBase):
    type: str = "echo"
    payload: Any


class CommandMessage(MessageBase):
    type: str = "command"
    job_id: str
    command: str
