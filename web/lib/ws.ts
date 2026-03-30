export type WsConnectedEvent = {
    type: "connected";
    channel: "client" | "agent";
};

export type WsAuthOkEvent = {
    type: "auth_ok";
    role: string;
};

export type WsHostsSnapshotEvent = {
    type: "hosts_snapshot";
    hosts: Array<{
        id: string;
        name: string;
        state: "online" | "offline" | "waking" | "shutting_down" | "unknown";
        is_managed: boolean;
    }>;
};

export type WsHostStatusChangedEvent = {
    type: "host_status_changed";
    host_id: string;
    state: "online" | "offline" | "waking" | "shutting_down" | "unknown";
};

export type WsJobUpdateEvent = {
    type: "job_update";
    job_id: string;
    status: "pending" | "running" | "completed" | "failed";
    host_id: string;
    command: string;
    message: string;
};

export type WsAgentHeartbeatEvent = {
    type: "agent_heartbeat";
    host_id: string;
};

export type WsErrorEvent = {
    type: "error";
    message: string;
};

export type WsServerEvent =
    | WsConnectedEvent
    | WsAuthOkEvent
    | WsHostsSnapshotEvent
    | WsHostStatusChangedEvent
    | WsJobUpdateEvent
    | WsAgentHeartbeatEvent
    | WsErrorEvent;

function createRequestId(): string {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
        return crypto.randomUUID();
    }

    return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export class ControlPlaneWsClient {
    private websocket: WebSocket | null = null;
    private readonly onEvent: (event: WsServerEvent) => void;

    constructor(onEvent: (event: WsServerEvent) => void) {
        this.onEvent = onEvent;
    }

    connect(): void {
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        const url = `${protocol}://${window.location.host}/ws/client`;

        this.websocket = new WebSocket(url);

        this.websocket.onmessage = (messageEvent) => {
            try {
                const parsed = JSON.parse(messageEvent.data) as WsServerEvent;
                this.onEvent(parsed);
            } catch (error) {
                console.error("Failed to parse WS message", error);
            }
        };

        this.websocket.onerror = (error) => {
            console.error("WebSocket error", error);
        };

        this.websocket.onclose = () => {
            this.websocket = null;
        };
    }

    disconnect(): void {
        if (!this.websocket) {
            return;
        }

        this.websocket.close();
        this.websocket = null;
    }

    sendCommand(hostName: string, command: "wake" | "shutdown" | "reboot"): void {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            console.error("WebSocket is not connected");
            return;
        }

        this.websocket.send(
            JSON.stringify({
                type: "command_request",
                request_id: createRequestId(),
                host_id: hostName,
                command,
            }),
        );
    }
}
