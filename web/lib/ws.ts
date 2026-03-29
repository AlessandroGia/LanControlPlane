import { config } from "./config";
import type { HostState, JobStatus } from "./types";

export type WsServerEvent =
    | { type: "connected"; channel: string }
    | { type: "auth_ok"; role: string }
    | {
        type: "hosts_snapshot";
        hosts: Array<{
            id: string;
            name: string;
            state: HostState;
            is_managed: boolean;
        }>;
    }
    | {
        type: "host_status_changed";
        host_id: string;
        state: HostState;
    }
    | {
        type: "job_update";
        job_id: string;
        status: JobStatus;
        host_id: string;
        command: string;
        message: string | null;
    }
    | {
        type: "error";
        message: string;
    };

export class ControlPlaneWsClient {
    private socket: WebSocket | null = null;
    private readonly onEvent: (event: WsServerEvent) => void;

    constructor(onEvent: (event: WsServerEvent) => void) {
        this.onEvent = onEvent;
    }

    connect(): void {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            return;
        }

        const wsUrl = config.getWsClientUrl();
        if (!wsUrl) {
            console.error("WS URL is empty");
            return;
        }

        this.socket = new WebSocket(wsUrl);

        this.socket.onmessage = (event: MessageEvent<string>) => {
            try {
                const payload = JSON.parse(event.data) as WsServerEvent;
                this.onEvent(payload);
            } catch (error) {
                console.error("Invalid WS payload", error);
            }
        };

        this.socket.onerror = (error) => {
            console.error("WS error", error);
        };

        this.socket.onclose = () => {
            this.socket = null;
        };
    }

    disconnect(): void {
        this.socket?.close();
        this.socket = null;
    }

    sendCommand(hostName: string, command: "wake" | "shutdown" | "reboot"): void {
        this.send({
            type: "command_request",
            request_id: crypto.randomUUID(),
            host_id: hostName,
            command,
        });
    }

    private send(payload: object): void {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            console.warn("WS not connected");
            return;
        }

        this.socket.send(JSON.stringify(payload));
    }
}
