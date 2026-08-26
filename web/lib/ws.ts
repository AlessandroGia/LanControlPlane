import { config } from "./config";

export type WsConnectionState = "connecting" | "ready" | "reconnecting" | "disconnected";

export type WsServerEvent =
    | { type: "auth_ok"; role: string }
    | {
        type: "hosts_snapshot";
        hosts: Array<{
            id: string;
            name: string;
            state: "online" | "offline" | "waking" | "shutting_down" | "unknown";
            is_managed: boolean;
        }>;
    }
    | {
        type: "host_status_changed";
        host_id: string;
        state: "online" | "offline" | "waking" | "shutting_down" | "unknown";
    }
    | {
        type: "job_update";
        job_id: string;
        status: "pending" | "running" | "completed" | "failed";
        host_id: string;
        command: string;
        message: string | null;
    }
    | { type: "agent_heartbeat"; host_id: string }
    | { type: "error"; message: string };

function createRequestId(): string {
    return crypto.randomUUID();
}

export class ControlPlaneWsClient {
    private websocket: WebSocket | null = null;
    private reconnectTimer: number | null = null;
    private reconnectAttempt = 0;
    private shouldReconnect = true;
    private readonly onEvent: (event: WsServerEvent) => void;
    private readonly onStateChange: (state: WsConnectionState) => void;

    constructor(
        onEvent: (event: WsServerEvent) => void,
        onStateChange: (state: WsConnectionState) => void,
    ) {
        this.onEvent = onEvent;
        this.onStateChange = onStateChange;
    }

    connect(): void {
        this.shouldReconnect = true;
        this.openSocket(false);
    }

    private openSocket(isReconnect: boolean): void {
        if (
            this.websocket &&
            (this.websocket.readyState === WebSocket.CONNECTING ||
                this.websocket.readyState === WebSocket.OPEN)
        ) {
            return;
        }

        this.onStateChange(isReconnect ? "reconnecting" : "connecting");
        const websocket = new WebSocket(config.getWsClientUrl());
        this.websocket = websocket;

        websocket.onmessage = (messageEvent: MessageEvent<string>) => {
            try {
                const parsed = JSON.parse(messageEvent.data) as WsServerEvent;
                if (parsed.type === "auth_ok") {
                    this.reconnectAttempt = 0;
                    this.onStateChange("ready");
                } else if (parsed.type === "error" && parsed.message === "Not authenticated") {
                    this.shouldReconnect = false;
                    this.onStateChange("disconnected");
                }
                this.onEvent(parsed);
            } catch (error) {
                console.error("Failed to parse WebSocket message", error);
            }
        };

        websocket.onerror = () => {
            // onclose owns reconnect scheduling and user-visible state.
        };

        websocket.onclose = () => {
            if (this.websocket === websocket) {
                this.websocket = null;
            }
            if (!this.shouldReconnect) {
                this.onStateChange("disconnected");
                return;
            }
            this.scheduleReconnect();
        };
    }

    private scheduleReconnect(): void {
        if (this.reconnectTimer !== null) {
            return;
        }

        const delay = Math.min(1000 * 2 ** this.reconnectAttempt, 30000);
        this.reconnectAttempt += 1;
        this.onStateChange("reconnecting");
        this.reconnectTimer = window.setTimeout(() => {
            this.reconnectTimer = null;
            this.openSocket(true);
        }, delay);
    }

    disconnect(): void {
        this.shouldReconnect = false;
        if (this.reconnectTimer !== null) {
            window.clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        this.websocket?.close();
        this.websocket = null;
        this.onStateChange("disconnected");
    }

    sendCommand(hostName: string, command: "wake" | "shutdown" | "reboot"): boolean {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            return false;
        }

        this.websocket.send(
            JSON.stringify({
                type: "command_request",
                request_id: createRequestId(),
                host_id: hostName,
                command,
            }),
        );
        return true;
    }
}
