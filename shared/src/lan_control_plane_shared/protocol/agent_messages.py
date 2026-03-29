from lan_control_plane_shared.protocol.base import MessageBase
from pydantic import BaseModel, ConfigDict


class AgentMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cpu: float
    memory: float


class AgentHello(BaseModel):
    type: str = "hello"
    agent_id: str
    token: str
    hostname: str
    version: str
    ip_address: str | None = None
    mac_address: str | None = None


class AgentHeartbeat(MessageBase):
    type: str = "heartbeat"
    agent_id: str
    uptime: int
    metrics: AgentMetrics


class AgentAck(MessageBase):
    type: str = "ack"
    job_id: str


class AgentResult(MessageBase):
    type: str = "result"
    job_id: str
    status: str
    message: str
