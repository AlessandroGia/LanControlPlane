"use client";

import { isOlderThan } from "@/lib/time";
import type { Agent, Host, HostLatestMetric } from "@/lib/types";
import { useHydrated } from "@/lib/use-hydrated";

type DashboardSummaryProps = {
    hosts: Host[];
    agents: Agent[];
    latestMetrics: HostLatestMetric[];
};

function SummaryTile({
    label,
    value,
}: {
    label: string;
    value: number;
}) {
    return (
        <div className="summary-tile">
            <div className="summary-tile-label">{label}</div>
            <div className="summary-tile-value">{value}</div>
        </div>
    );
}

export function DashboardSummary({
    hosts,
    agents,
    latestMetrics,
}: DashboardSummaryProps) {
    const hydrated = useHydrated();

    const onlineCount = hosts.filter((host) => host.state === "online").length;
    const offlineCount = hosts.filter((host) => host.state === "offline").length;
    const wakingCount = hosts.filter((host) => host.state === "waking").length;

    const staleCount = hydrated
        ? hosts.filter((host) => {
            const agent = agents.find((item) => item.host_name === host.name);
            const metric = latestMetrics.find((item) => item.host_name === host.name);

            const agentStale = agent?.last_seen_at
                ? isOlderThan(agent.last_seen_at, 60)
                : false;

            const metricStale = metric?.collected_at
                ? isOlderThan(metric.collected_at, 120)
                : false;

            return agentStale || metricStale;
        }).length
        : 0;

    return (
        <section className="dashboard-summary">
            <SummaryTile label="Total" value={hosts.length} />
            <SummaryTile label="Online" value={onlineCount} />
            <SummaryTile label="Offline" value={offlineCount} />
            <SummaryTile label="Waking" value={wakingCount} />
            <SummaryTile label="Stale" value={staleCount} />
        </section>
    );
}
