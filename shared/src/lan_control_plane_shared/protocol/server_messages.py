from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from lan_control_plane_shared.enums.host_state import HostState
from lan_control_plane_shared.enums.job_status import JobStatus
from lan_control_plane_shared.protocol.base import MessageBase


class HostSnapshotItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    state: HostState
    is_managed: bool


class AuthOk(MessageBase):
    type: Literal["auth_ok"] = "auth_ok"
    role: str


class Connected(MessageBase):
    type: Literal["connected"] = "connected"
    channel: str


class HostsSnapshot(MessageBase):
    type: Literal["hosts_snapshot"] = "hosts_snapshot"
    hosts: list[HostSnapshotItem]


class HostStatusChanged(MessageBase):
    type: Literal["host_status_changed"] = "host_status_changed"
    host_id: str
    state: HostState


class JobUpdate(MessageBase):
    type: Literal["job_update"] = "job_update"
    job_id: str
    status: JobStatus
    host_id: str
    command: str
    message: str | None = None


class ErrorMessage(MessageBase):
    type: Literal["error"] = "error"
    message: str


class EchoMessage(MessageBase):
    type: Literal["echo"] = "echo"
    payload: Any


class CommandMessage(MessageBase):
    type: Literal["command"] = "command"
    job_id: str
    command: str
