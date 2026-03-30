"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AuditPanel } from "@/components/dashboard/audit-panel";
import { type HostFilterValue } from "@/components/dashboard/dashboard-filters";
import { HostList } from "@/components/dashboard/host-list";
import { JobsPanel } from "@/components/dashboard/jobs-panel";
import { getAgents, getAuditLogs, getHosts, getJobs, getLatestMetrics } from "@/lib/api";
import { isOlderThan } from "@/lib/time";
import type { Agent, AuditLog, Host, HostLatestMetric, Job } from "@/lib/types";
import { useHydrated } from "@/lib/use-hydrated";
import { ControlPlaneWsClient, type WsServerEvent } from "@/lib/ws";
import { DashboardSummary } from "@/components/dashboard/dashboard-summary";


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
    const fastRefreshPendingRef = useRef(false);

    const fullRefreshInFlightRef = useRef(false);
    const fullRefreshPendingRef = useRef(false);

    const scheduledFastRefreshRef = useRef<number | null>(null);

    const hydrated = useHydrated();
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState<HostFilterValue>("all");

    const clearPendingForHost = useCallback((hostName: string): void => {
        setPendingCommands((current) => {
            const next = { ...current };
            delete next[hostName];
            return next;
        });
    }, []);

    const refreshFastData = useCallback(async (): Promise<void> => {
        if (fastRefreshInFlightRef.current) {
            fastRefreshPendingRef.current = true;
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

            if (fastRefreshPendingRef.current) {
                fastRefreshPendingRef.current = false;
                void refreshFastData();
            }
        }
    }, []);

    const refreshFullData = useCallback(async (): Promise<void> => {
        if (fullRefreshInFlightRef.current) {
            fullRefreshPendingRef.current = true;
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

            if (fullRefreshPendingRef.current) {
                fullRefreshPendingRef.current = false;
                void refreshFullData();
            }
        }
    }, []);

    const scheduleFastRefresh = useCallback((): void => {
        if (scheduledFastRefreshRef.current !== null) {
            return;
        }

        scheduledFastRefreshRef.current = window.setTimeout(() => {
            scheduledFastRefreshRef.current = null;
            void refreshFastData();
        }, 800);
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

            if (scheduledFastRefreshRef.current !== null) {
                window.clearTimeout(scheduledFastRefreshRef.current);
                scheduledFastRefreshRef.current = null;
            }
        };
    }, [handleWsEvent, refreshFullData]);

    useEffect(() => {
        const intervalId = window.setInterval(() => {
            void refreshFastData();
        }, 10000);

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

    const filteredHosts = useMemo(() => {
        const normalizedSearch = search.trim().toLowerCase();

        return hosts.filter((host) => {
            const agent = agents.find((item) => item.host_name === host.name);
            const metric = latestMetrics.find((item) => item.host_name === host.name);

            const matchesSearch =
                normalizedSearch.length === 0 ||
                host.name.toLowerCase().includes(normalizedSearch) ||
                (host.ip_address ?? "").toLowerCase().includes(normalizedSearch) ||
                (host.mac_address ?? "").toLowerCase().includes(normalizedSearch);

            if (!matchesSearch) {
                return false;
            }

            if (statusFilter === "all") {
                return true;
            }

            if (statusFilter === "stale") {
                if (!hydrated) {
                    return false;
                }

                const agentStale = agent?.last_seen_at
                    ? isOlderThan(agent.last_seen_at, 60)
                    : false;

                const metricStale = metric?.collected_at
                    ? isOlderThan(metric.collected_at, 120)
                    : false;

                return agentStale || metricStale;
            }

            return host.state === statusFilter;
        });
    }, [agents, hosts, hydrated, latestMetrics, search, statusFilter]);

    return (

        <DashboardSummary
        hosts={hosts}
        agents={agents}
        latestMetrics={latestMetrics}
        />

        <DashboardFilters
        search={search}
        statusFilter={statusFilter}
        onSearchChange={setSearch}
        onStatusFilterChange={setStatusFilter}
        />

        <div className="dashboard-grid">
            <div className="left-column">
                <HostList
                hosts={filteredHosts}
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
