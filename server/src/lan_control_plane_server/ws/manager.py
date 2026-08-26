import logging
import time

from fastapi import WebSocket
from lan_control_plane_shared.enums.host_state import HostState
from lan_control_plane_shared.enums.job_status import JobStatus
from lan_control_plane_shared.protocol.server_messages import HostStatusChanged, JobUpdate

LOGGER = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.agent_connections: dict[str, WebSocket] = {}
        self.agent_last_activity: dict[str, float] = {}
        self.client_connections: set[WebSocket] = set()

    def has_agent(self, agent_id: str) -> bool:
        return agent_id in self.agent_connections

    def is_agent_connection(self, agent_id: str, websocket: WebSocket) -> bool:
        return self.agent_connections.get(agent_id) is websocket

    def connect_agent(self, agent_id: str, websocket: WebSocket) -> bool:
        existing = self.agent_connections.get(agent_id)
        if existing is not None and existing is not websocket:
            return False
        self.agent_connections[agent_id] = websocket
        self.agent_last_activity[agent_id] = time.monotonic()
        return True

    def touch_agent(self, agent_id: str, websocket: WebSocket) -> None:
        if self.is_agent_connection(agent_id, websocket):
            self.agent_last_activity[agent_id] = time.monotonic()

    def get_stale_agents(self, timeout_seconds: int) -> list[tuple[str, WebSocket]]:
        cutoff = time.monotonic() - timeout_seconds
        return [
            (agent_id, websocket)
            for agent_id, websocket in tuple(self.agent_connections.items())
            if self.agent_last_activity.get(agent_id, 0) < cutoff
        ]

    def disconnect_agent(self, agent_id: str, websocket: WebSocket) -> bool:
        if self.agent_connections.get(agent_id) is not websocket:
            return False
        self.agent_connections.pop(agent_id, None)
        self.agent_last_activity.pop(agent_id, None)
        return True

    def clear(self) -> None:
        self.agent_connections.clear()
        self.agent_last_activity.clear()
        self.client_connections.clear()

    def connect_client(self, websocket: WebSocket) -> None:
        self.client_connections.add(websocket)

    def disconnect_client(self, websocket: WebSocket) -> None:
        self.client_connections.discard(websocket)

    async def _broadcast(self, payload: dict[str, object]) -> None:
        stale_clients: list[WebSocket] = []
        for client in tuple(self.client_connections):
            try:
                await client.send_json(payload)
            except Exception:
                LOGGER.warning("Removing an unreachable dashboard WebSocket", exc_info=True)
                stale_clients.append(client)

        for client in stale_clients:
            self.disconnect_client(client)

    async def broadcast_host_status(self, host_id: str, state: HostState) -> None:
        message = HostStatusChanged(host_id=host_id, state=state)
        await self._broadcast(message.model_dump(mode="json"))

    async def broadcast_job_update(
        self,
        *,
        job_id: str,
        status: JobStatus,
        host_id: str,
        command: str,
        message: str | None = None,
    ) -> None:
        payload = JobUpdate(
            job_id=job_id,
            status=status,
            host_id=host_id,
            command=command,
            message=message,
        )
        await self._broadcast(payload.model_dump(mode="json"))

    async def broadcast_agent_heartbeat(self, host_id: str) -> None:
        await self._broadcast({"type": "agent_heartbeat", "host_id": host_id})

    async def send_command_to_agent(self, agent_id: str, payload: dict[str, object]) -> bool:
        websocket = self.agent_connections.get(agent_id)
        if websocket is None:
            return False

        try:
            await websocket.send_json(payload)
        except Exception:
            LOGGER.warning("Failed to send a command to agent %s", agent_id, exc_info=True)
            self.disconnect_agent(agent_id, websocket)
            return False
        return True


manager = ConnectionManager()
