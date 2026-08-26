"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { AuditPanel } from "@/components/dashboard/audit-panel";
import { DashboardFilters, type HostFilterValue } from "@/components/dashboard/dashboard-filters";
import { DashboardSummary } from "@/components/dashboard/dashboard-summary";
import { HostList } from "@/components/dashboard/host-list";
import { JobsPanel } from "@/components/dashboard/jobs-panel";
import { CollapsiblePanel } from "@/components/ui/collapsible-panel";
import { deleteHost, getAgents, getAuditLogs, getHosts, getJobs, getLatestMetrics } from "@/lib/api";
import { isOlderThan } from "@/lib/time";
import type { Agent, AuditLog, Host, HostLatestMetric, Job } from "@/lib/types";
import { useHydrated } from "@/lib/use-hydrated";
import {
    ControlPlaneWsClient,
    type WsConnectionState,
    type WsServerEvent,
} from "@/lib/ws";


type DashboardClientProps = {
    currentUser: { username: string; role: string };
    initialError?: string | null;
    hosts: Host[];
    jobs: Job[];
    agents: Agent[];
    auditLogs: AuditLog[];
    latestMetrics: HostLatestMetric[];
};

type PendingCommandMap = Record<string, "wake" | "shutdown" | "reboot" | undefined>;

export function DashboardClient({
    currentUser,
    initialError = null,
    hosts: initialHosts,
    jobs: initialJobs,
    agents: initialAgents,
    auditLogs: initialAuditLogs,
    latestMetrics: initialLatestMetrics,
}: DashboardClientProps) {
    const router = useRouter();
    const [hosts, setHosts] = useState<Host[]>(initialHosts);
    const [jobs, setJobs] = useState<Job[]>(initialJobs);
    const [agents, setAgents] = useState<Agent[]>(initialAgents);
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>(initialAuditLogs);
    const [latestMetrics, setLatestMetrics] = useState<HostLatestMetric[]>(initialLatestMetrics);

    const [connectionState, setConnectionState] =
        useState<WsConnectionState>("connecting");
    const [refreshError, setRefreshError] = useState<string | null>(initialError);
    const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
    const [pendingCommands, setPendingCommands] = useState<PendingCommandMap>({});
    const [confirmation, setConfirmation] = useState<{
        hostName: string;
        command: "shutdown" | "reboot";
    } | null>(null);
    const [deleteConfirmation, setDeleteConfirmation] = useState<string | null>(null);

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
            do {
                fastRefreshPendingRef.current = false;
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

                if (results.some((result) => result.status === "fulfilled")) {
                    setRefreshError(null);
                    setLastUpdatedAt(new Date());
                } else {
                    setRefreshError("Unable to refresh host data. Retrying automatically.");
                }
            } while (fastRefreshPendingRef.current);
        } finally {
            fastRefreshInFlightRef.current = false;
        }
    }, []);

    const refreshFullData = useCallback(async (): Promise<void> => {
        if (fullRefreshInFlightRef.current) {
            fullRefreshPendingRef.current = true;
            return;
        }

        fullRefreshInFlightRef.current = true;

        try {
            do {
                fullRefreshPendingRef.current = false;
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

                if (results.some((result) => result.status === "fulfilled")) {
                    setRefreshError(null);
                    setLastUpdatedAt(new Date());
                } else {
                    setRefreshError("Unable to refresh dashboard data. Retrying automatically.");
                }
            } while (fullRefreshPendingRef.current);
        } finally {
            fullRefreshInFlightRef.current = false;
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
            if (event.type === "auth_ok") {
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
                if (event.message === "Not authenticated") {
                    router.push("/login");
                    return;
                }
                setRefreshError(event.message);
            }
        },
        [clearPendingForHost, refreshFullData, router, scheduleFastRefresh],
    );

    useEffect(() => {
        const client = new ControlPlaneWsClient(handleWsEvent, setConnectionState);
        wsClientRef.current = client;
        client.connect();

        void refreshFullData();

        return () => {
            client.disconnect();
            wsClientRef.current = null;

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

    const actionsDisabled = useMemo(
        () => connectionState !== "ready" || currentUser.role !== "admin",
        [connectionState, currentUser.role],
    );

    function sendCommand(hostName: string, command: "wake" | "shutdown" | "reboot"): void {
        if (!wsClientRef.current) {
            return;
        }

        const sent = wsClientRef.current.sendCommand(hostName, command);
        if (!sent) {
            setRefreshError("The live connection is unavailable. The command was not sent.");
            return;
        }

        setPendingCommands((current) => ({ ...current, [hostName]: command }));
    }

    function handleWake(hostName: string): void {
        sendCommand(hostName, "wake");
    }

    function handleShutdown(hostName: string): void {
        setConfirmation({ hostName, command: "shutdown" });
    }

    function handleReboot(hostName: string): void {
        setConfirmation({ hostName, command: "reboot" });
    }

    async function handleDeleteConfirmed(hostName: string): Promise<void> {
        try {
            await deleteHost(hostName);
            setHosts((current) => current.filter((host) => host.name !== hostName));
            setAgents((current) => current.filter((agent) => agent.host_name !== hostName));
            setLatestMetrics((current) => current.filter((metric) => metric.host_name !== hostName));
            setDeleteConfirmation(null);
            setRefreshError(null);
            void refreshFullData();
        } catch (error) {
            console.error("Failed to remove host", error);
            setRefreshError("Unable to remove this host. Disconnect its agent and try again.");
        }
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

                const agentStale = !agent?.last_seen_at || isOlderThan(agent.last_seen_at, 60);

                const metricStale =
                    !metric?.collected_at || isOlderThan(metric.collected_at, 120);

                return agentStale || metricStale;
            }

            return host.state === statusFilter;
        });
    }, [agents, hosts, hydrated, latestMetrics, search, statusFilter]);

    return (
        <>
            <section className="dashboard-status" aria-live="polite">
                <div>
                    <span className={`connection-dot ${connectionState}`} />
                    Live connection: {connectionState}
                </div>
                <div>
                    Signed in as {currentUser.username} ({currentUser.role})
                    {lastUpdatedAt ? ` · Updated ${lastUpdatedAt.toLocaleTimeString()}` : ""}
                </div>
            </section>

            {refreshError ? (
                <div className="dashboard-alert" role="alert">
                    <span>{refreshError}</span>
                    <button type="button" onClick={() => void refreshFullData()}>
                        Retry now
                    </button>
                </div>
            ) : null}

            {currentUser.role !== "admin" ? (
                <div className="dashboard-notice">
                    This account has read-only access. Host control actions require an administrator.
                </div>
            ) : null}

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
                        onDelete={setDeleteConfirmation}
                        canDelete={currentUser.role === "admin"}
                        actionsDisabled={actionsDisabled}
                        pendingCommands={pendingCommands}
                    />
                </div>

                <div className="right-column">
                    <CollapsiblePanel title="Recent jobs" count={jobs.length} defaultOpen={false}>
                        <JobsPanel jobs={jobs} />
                    </CollapsiblePanel>

                    <CollapsiblePanel title="Audit logs" count={auditLogs.length} defaultOpen={false}>
                        <AuditPanel logs={auditLogs} />
                    </CollapsiblePanel>
                </div>
            </div>

            {confirmation ? (
                <div className="confirmation-backdrop" role="presentation">
                    <section
                        className="confirmation-dialog"
                        role="alertdialog"
                        aria-modal="true"
                        aria-labelledby="confirmation-title"
                    >
                        <h2 id="confirmation-title">Confirm {confirmation.command}</h2>
                        <p>
                            Send <strong>{confirmation.command}</strong> to{" "}
                            <strong>{confirmation.hostName}</strong>? This can interrupt active work.
                        </p>
                        <div className="confirmation-actions">
                            <button type="button" onClick={() => setConfirmation(null)}>
                                Cancel
                            </button>
                            <button
                                type="button"
                                className="danger-confirm-button"
                                onClick={() => {
                                    sendCommand(confirmation.hostName, confirmation.command);
                                    setConfirmation(null);
                                }}
                            >
                                Confirm {confirmation.command}
                            </button>
                        </div>
                    </section>
                </div>
            ) : null}

            {deleteConfirmation ? (
                <div className="confirmation-backdrop" role="presentation">
                    <section
                        className="confirmation-dialog"
                        role="alertdialog"
                        aria-modal="true"
                        aria-labelledby="delete-confirmation-title"
                    >
                        <h2 id="delete-confirmation-title">Remove host</h2>
                        <p>
                            Permanently remove <strong>{deleteConfirmation}</strong> and its stored
                            agent, jobs, and metrics? Audit history is retained.
                        </p>
                        <div className="confirmation-actions">
                            <button type="button" onClick={() => setDeleteConfirmation(null)}>
                                Cancel
                            </button>
                            <button
                                type="button"
                                className="danger-confirm-button"
                                onClick={() => void handleDeleteConfirmed(deleteConfirmation)}
                            >
                                Remove host
                            </button>
                        </div>
                    </section>
                </div>
            ) : null}
        </>
    );
}
