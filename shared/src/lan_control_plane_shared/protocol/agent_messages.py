from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

from lan_control_plane_shared.protocol.base import MessageBase


class AgentMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cpu: float = Field(ge=0, le=100)
    memory: float = Field(ge=0, le=100)


class AgentHello(MessageBase):
    type: Literal["hello"] = "hello"
    agent_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    token: str = Field(min_length=16, max_length=512)
    enrollment_token: str | None = Field(default=None, min_length=16, max_length=512)
    hostname: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=50)
    ip_address: IPvAnyAddress | None = None
    mac_address: str | None = Field(default=None, max_length=17)


class AgentHeartbeat(MessageBase):
    type: Literal["heartbeat"] = "heartbeat"
    agent_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    uptime: int = Field(ge=0)
    metrics: AgentMetrics


class AgentAck(MessageBase):
    type: Literal["ack"] = "ack"
    job_id: str = Field(min_length=36, max_length=36)


class AgentResult(MessageBase):
    type: Literal["result"] = "result"
    job_id: str = Field(min_length=36, max_length=36)
    status: Literal["ok", "error"]
    message: str = Field(max_length=4096)
