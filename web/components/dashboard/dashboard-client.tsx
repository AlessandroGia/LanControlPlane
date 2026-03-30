"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AuditPanel } from "@/components/dashboard/audit-panel";
import { HostList } from "@/components/dashboard/host-list";
import { JobsPanel } from "@/components/dashboard/jobs-panel";
import { getAgents, getAuditLogs, getHosts, getJobs, getLatestMetrics } from "@/lib/api";
import type { Agent, AuditLog, Host, HostLatestMetric, Job } from "@/lib/types";
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
    const [latestMetrics, setLatestMetrics] = useState<HostLatestMetric[]>(initialLatestMetrics);

    const [isWsReady, setIsWsReady] = useState(false);
    const [pendingCommands, setPendingCommands] = useState<PendingCommandMap>({});

    const wsClientRef = useRef<ControlPlaneWsClient | null>(null);
    const fastRefreshInFlightRef = useRef(false);
    const fullRefreshInFlightRef = useRef(false);
    const scheduledRefreshRef = useRef<number | null>(null);

    const clearPendingForHost = useCallback((hostName: string): void => {
        setPendingCommands((current) => {
            const next = { ...current };
            delete next[hostName];
            return next;
        });
    }, []);

    const refreshFastData = useCallback(async (): Promise<void> => {
        if (fastRefreshInFlightRef.current) {
            return;
        }

        fastRefreshInFlightRef.current = true;

        try {
            const results = await Promise.allSettled([
                getHosts(),
                getAgents(),
                getLatestMetrics(),
            ]);

            const [hostsResult, agentsResult, metricsResult] = results;

            if (hostsResult.status === "fulfilled") {
                setHosts(hostsResult.value);
            } else {
                console.error("Failed to refresh hosts", hostsResult.reason);
            }

            if (agentsResult.status === "fulfilled") {
                setAgents(agentsResult.value);
            } else {
                console.error("Failed to refresh agents", agentsResult.reason);
            }

            if (metricsResult.status === "fulfilled") {
                setLatestMetrics(metricsResult.value);
            } else {
                console.error("Failed to refresh latest metrics", metricsResult.reason);
            }
        } catch (error) {
            console.error("Failed to refresh fast dashboard data", error);
        } finally {
            fastRefreshInFlightRef.current = false;
        }
    }, []);

    const refreshFullData = useCallback(async (): Promise<void> => {
        if (fullRefreshInFlightRef.current) {
            return;
        }

        fullRefreshInFlightRef.current = true;

        try {
            const results = await Promise.allSettled([
                getHosts(),
                getJobs(),
                getAgents(),
                getAuditLogs(),
                getLatestMetrics(),
            ]);

            const [hostsResult, jobsResult, agentsResult, auditLogsResult, metricsResult] = results;

            if (hostsResult.status === "fulfilled") {
                setHosts(hostsResult.value);
            } else {
                console.error("Failed to refresh hosts", hostsResult.reason);
            }

            if (jobsResult.status === "fulfilled") {
                setJobs(jobsResult.value);
            } else {
                console.error("Failed to refresh jobs", jobsResult.reason);
            }

            if (agentsResult.status === "fulfilled") {
                setAgents(agentsResult.value);
            } else {
                console.error("Failed to refresh agents", agentsResult.reason);
            }

            if (auditLogsResult.status === "fulfilled") {
                setAuditLogs(auditLogsResult.value);
            } else {
                console.error("Failed to refresh audit logs", auditLogsResult.reason);
            }

            if (metricsResult.status === "fulfilled") {
                setLatestMetrics(metricsResult.value);
            } else {
                console.error("Failed to refresh latest metrics", metricsResult.reason);
            }
        } catch (error) {
            console.error("Failed to refresh full dashboard data", error);
        } finally {
            fullRefreshInFlightRef.current = false;
        }
    }, []);

    const scheduleFastRefresh = useCallback((): void => {
        if (scheduledRefreshRef.current !== null) {
            return;
        }

        scheduledRefreshRef.current = window.setTimeout(() => {
            scheduledRefreshRef.current = null;
            void refreshFastData();
        }, 500);
    }, [refreshFastData]);

    const handleWsEvent = useCallback(
        (event: WsServerEvent): void => {
            if (event.type === "connected") {
                return;
            }

            if (event.type === "auth_ok") {
                setIsWsReady(true);
                void refreshFullData();
                return;
            }

            if (event.type === "hosts_snapshot") {
                scheduleFastRefresh();
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

                scheduleFastRefresh();
                return;
            }

            if (event.type === "agent_heartbeat") {
                scheduleFastRefresh();
                return;
            }

            if (event.type === "job_update") {
                if (event.status === "failed" || event.status === "completed") {
                    clearPendingForHost(event.host_id);
                }

                void refreshFullData();
                return;
            }

            if (event.type === "error") {
                console.error("WS server error:", event.message);
            }
        },
        [clearPendingForHost, refreshFullData, scheduleFastRefresh],
    );

    useEffect(() => {
        const client = new ControlPlaneWsClient(handleWsEvent);
        wsClientRef.current = client;
        client.connect();

        void refreshFullData();

        return () => {
            client.disconnect();
            wsClientRef.current = null;
            setIsWsReady(false);

            if (scheduledRefreshRef.current !== null) {
                window.clearTimeout(scheduledRefreshRef.current);
                scheduledRefreshRef.current = null;
            }
        };
    }, [handleWsEvent, refreshFullData]);

    useEffect(() => {
        const intervalId = window.setInterval(() => {
            void refreshFastData();
        }, 5000);

        return () => {
            window.clearInterval(intervalId);
        };
    }, [refreshFastData]);

    useEffect(() => {
        const intervalId = window.setInterval(() => {
            void refreshFullData();
        }, 30000);

        return () => {
            window.clearInterval(intervalId);
        };
    }, [refreshFullData]);

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
