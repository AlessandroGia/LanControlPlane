"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AuditPanel } from "@/components/dashboard/audit-panel";
import { HostList } from "@/components/dashboard/host-list";
import { JobsPanel } from "@/components/dashboard/jobs-panel";
import { getAgents, getAuditLogs, getHosts, getJobs, getLatestMetrics } from "@/lib/api";
import type {
    Agent,
    AuditLog,
    Host,
    HostLatestMetric,
    Job,
} from "@/lib/types";
import { ControlPlaneWsClient, type WsServerEvent } from "@/lib/ws";

type DashboardClientProps = {
    hosts: Host[];
    jobs: Job[];
    agents: Agent[];
    auditLogs: AuditLog[];
    latestMetrics: HostLatestMetric[];
};

type PendingCommandMap = Record<string, "wake" | "shutdown" | "reboot" | undefined>;

export function DashboardClient({
    hosts: initialHosts,
    jobs: initialJobs,
    agents: initialAgents,
    auditLogs: initialAuditLogs,
    latestMetrics: initialLatestMetrics,
}: DashboardClientProps) {
    const [hosts, setHosts] = useState<Host[]>(initialHosts);
    const [jobs, setJobs] = useState<Job[]>(initialJobs);
    const [agents, setAgents] = useState<Agent[]>(initialAgents);
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>(initialAuditLogs);
    const [latestMetrics, setLatestMetrics] =
        useState<HostLatestMetric[]>(initialLatestMetrics);

    const [isWsReady, setIsWsReady] = useState(false);
    const [pendingCommands, setPendingCommands] = useState<PendingCommandMap>({});

    const wsClientRef = useRef<ControlPlaneWsClient | null>(null);
    const refreshInFlightRef = useRef(false);

    const clearPendingForHost = useCallback((hostName: string): void => {
        setPendingCommands((current) => {
            const next = { ...current };
            delete next[hostName];
            return next;
        });
    }, []);

    const refreshData = useCallback(async (): Promise<void> => {
        if (refreshInFlightRef.current) {
            return;
        }

        refreshInFlightRef.current = true;

        try {
            const [
                updatedHosts,
                updatedJobs,
                updatedAgents,
                updatedAuditLogs,
                updatedLatestMetrics,
            ] = await Promise.all([
                getHosts(),
                getJobs(),
                getAgents(),
                getAuditLogs(),
                getLatestMetrics(),
            ]);

            setHosts(updatedHosts);
            setJobs(updatedJobs);
            setAgents(updatedAgents);
            setAuditLogs(updatedAuditLogs);
            setLatestMetrics(updatedLatestMetrics);
        } catch (error) {
            console.error("Failed to refresh dashboard data", error);
        } finally {
            refreshInFlightRef.current = false;
        }
    }, []);

    const handleWsEvent = useCallback(
        (event: WsServerEvent): void => {
            if (event.type === "connected") {
                return;
            }

            if (event.type === "auth_ok") {
                setIsWsReady(true);
                void refreshData();
                return;
            }

            if (event.type === "hosts_snapshot") {
                void refreshData();
                return;
            }

            if (event.type === "host_status_changed") {
                if (
                    event.state === "waking" ||
                    event.state === "shutting_down" ||
                    event.state === "offline" ||
                    event.state === "online"
                ) {
                    clearPendingForHost(event.host_id);
                }

                void refreshData();
                return;
            }

            if (event.type === "job_update") {
                if (event.status === "failed" || event.status === "completed") {
                    clearPendingForHost(event.host_id);
                }

                void refreshData();
                return;
            }

            if (event.type === "error") {
                console.error("WS server error:", event.message);
            }
        },
        [clearPendingForHost, refreshData],
    );

    useEffect(() => {
        const client = new ControlPlaneWsClient(handleWsEvent);
        wsClientRef.current = client;
        client.connect();

        void refreshData();

        return () => {
            client.disconnect();
            wsClientRef.current = null;
            setIsWsReady(false);
        };
    }, [handleWsEvent, refreshData]);

    useEffect(() => {
        const intervalId = window.setInterval(() => {
            void refreshData();
        }, 15000);

        return () => {
            window.clearInterval(intervalId);
        };
    }, [refreshData]);

    const actionsDisabled = useMemo(() => !isWsReady, [isWsReady]);

    function sendCommand(hostName: string, command: "wake" | "shutdown" | "reboot"): void {
        if (!wsClientRef.current) {
            return;
        }

        setPendingCommands((current) => ({
            ...current,
            [hostName]: command,
        }));

        wsClientRef.current.sendCommand(hostName, command);
    }

    function handleWake(hostName: string): void {
        sendCommand(hostName, "wake");
    }

    function handleShutdown(hostName: string): void {
        sendCommand(hostName, "shutdown");
    }

    function handleReboot(hostName: string): void {
        sendCommand(hostName, "reboot");
    }

    return (
        <div className="dashboard-grid">
            <div className="left-column">
                <HostList
                    hosts={hosts}
                    agents={agents}
                    latestMetrics={latestMetrics}
                    onWake={handleWake}
                    onShutdown={handleShutdown}
                    onReboot={handleReboot}
                    actionsDisabled={actionsDisabled}
                    pendingCommands={pendingCommands}
                />
            </div>

            <div className="right-column">
                <JobsPanel jobs={jobs} />
                <AuditPanel logs={auditLogs} />
            </div>
        </div>
    );
}
