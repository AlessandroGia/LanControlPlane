from fastapi import WebSocket
from lan_control_plane_shared.enums.host_state import HostState
from lan_control_plane_shared.enums.job_status import JobStatus
from lan_control_plane_shared.protocol.server_messages import HostStatusChanged, JobUpdate


class ConnectionManager:
    def __init__(self) -> None:
        self.agent_connections: dict[str, WebSocket] = {}
        self.client_connections: set[WebSocket] = set()

    def has_agent(self, agent_id: str) -> bool:
        return agent_id in self.agent_connections

    async def connect_agent(self, agent_id: str, websocket: WebSocket) -> None:
        self.agent_connections[agent_id] = websocket

    def disconnect_agent(self, agent_id: str) -> None:
        self.agent_connections.pop(agent_id, None)

    async def connect_client(self, websocket: WebSocket) -> None:
        self.client_connections.add(websocket)

    def disconnect_client(self, websocket: WebSocket) -> None:
        self.client_connections.discard(websocket)

    async def broadcast_host_status(self, host_id: str, state: HostState) -> None:
        message = HostStatusChanged(host_id=host_id, state=state)
        stale_clients: list[WebSocket] = []

        for client in self.client_connections:
            try:
                await client.send_json(message.model_dump(mode="json"))
            except Exception:
                stale_clients.append(client)

        for client in stale_clients:
            self.disconnect_client(client)

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
        stale_clients: list[WebSocket] = []

        for client in self.client_connections:
            try:
                await client.send_json(payload.model_dump(mode="json"))
            except Exception:
                stale_clients.append(client)

        for client in stale_clients:
            self.disconnect_client(client)

    async def send_json_to_client(self, websocket: WebSocket, payload: dict[str, object]) -> None:
        await websocket.send_json(payload)

    async def send_command_to_agent(self, agent_id: str, payload: dict[str, object]) -> bool:
        websocket = self.agent_connections.get(agent_id)
        if websocket is None:
            return False

        await websocket.send_json(payload)
        return True


manager = ConnectionManager()
