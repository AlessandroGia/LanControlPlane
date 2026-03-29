import { LogoutButton } from "@/components/auth/logout-button";
import { HostMetricsChart } from "@/components/hosts/host-metrics-chart";
import { getAgents, getHost, getHostMetrics, getMe } from "@/lib/api";
import type { HostMetricRead } from "@/lib/types";
import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

function buildCookieHeader(
    cookieStore: Awaited<ReturnType<typeof cookies>>,
): string | undefined {
    const all = cookieStore.getAll();
    if (all.length === 0) {
        return undefined;
    }

    return all.map((cookie) => `${cookie.name}=${cookie.value}`).join("; ");
}

function formatDate(value: string): string {
    return new Date(value).toLocaleString();
}

function formatUptime(totalSeconds: number): string {
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);

    if (days > 0) {
        return `${days}d ${hours}h`;
    }

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }

    return `${minutes}m`;
}

function getLatestMetric(metrics: HostMetricRead[]): HostMetricRead | null {
    if (metrics.length === 0) {
        return null;
    }

    return [...metrics].sort(
        (a, b) =>
            new Date(b.collected_at).getTime() - new Date(a.collected_at).getTime(),
    )[0];
}

type PageProps = {
    params: Promise<{ name: string }>;
};

export default async function HostDetailPage({ params }: PageProps) {
    const { name } = await params;

    const cookieStore = await cookies();
    const cookieHeader = buildCookieHeader(cookieStore);

    if (!cookieHeader) {
        redirect("/login");
    }

    try {
        await getMe(cookieHeader);
    } catch {
        redirect("/login");
    }

    const [host, metrics, agents] = await Promise.all([
        getHost(name, cookieHeader),
        getHostMetrics(name, cookieHeader),
        getAgents(cookieHeader),
    ]);

    const agent = agents.find((item) => item.host_name === host.name);
    const latestMetric = getLatestMetric(metrics);

    return (
        <main className="container">
            <div className="page-header">
                <div>
                    <div className="page-subtitle" style={{ marginBottom: "0.5rem" }}>
                        <Link href="/">← Back to dashboard</Link>
                    </div>
                    <h1 className="page-title">{host.name}</h1>
                    <p className="page-subtitle">
                        Detailed host view with metrics and identity information.
                    </p>
                </div>

                <LogoutButton />
            </div>

            <div className="dashboard-grid">
                <div className="left-column">
                    <div className="panel">
                        <h2>Overview</h2>

                        <div className="list">
                            <div className="list-item">
                                <div className="list-item-title">State</div>
                                <div className="list-item-meta">{host.state}</div>
                            </div>

                            <div className="list-item">
                                <div className="list-item-title">Network</div>
                                <div className="list-item-meta">IP: {host.ip_address ?? "—"}</div>
                                <div className="list-item-meta">MAC: {host.mac_address ?? "—"}</div>
                            </div>

                            <div className="list-item">
                                <div className="list-item-title">Agent</div>
                                <div className="list-item-meta">
                                    {agent
                                        ? `${agent.version} · ${agent.enabled ? "enabled" : "disabled"}`
                                        : "No agent"}
                                </div>
                                {agent?.last_seen_at ? (
                                    <div className="list-item-meta">
                                        Last seen: {formatDate(agent.last_seen_at)}
                                    </div>
                                ) : null}
                            </div>

                            <div className="list-item">
                                <div className="list-item-title">Latest metrics</div>
                                {latestMetric ? (
                                    <>
                                        <div className="list-item-meta">
                                            CPU: {latestMetric.cpu_usage.toFixed(1)}%
                                        </div>
                                        <div className="list-item-meta">
                                            RAM: {latestMetric.memory_usage.toFixed(1)}%
                                        </div>
                                        <div className="list-item-meta">
                                            Uptime: {formatUptime(latestMetric.uptime_seconds)}
                                        </div>
                                        <div className="list-item-meta">
                                            Collected: {formatDate(latestMetric.collected_at)}
                                        </div>
                                    </>
                                ) : (
                                    <div className="list-item-meta">No metrics yet.</div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="right-column">
                    <div className="panel">
                        <h2>Metrics chart</h2>
                        <HostMetricsChart metrics={metrics} />
                    </div>
                    <div className="panel">
                        <h2>Recent metrics</h2>

                        {metrics.length === 0 ? (
                            <div className="list-item-meta">No metrics available.</div>
                        ) : (
                            <div className="list">
                                {[...metrics]
                                    .sort(
                                        (a, b) =>
                                            new Date(b.collected_at).getTime() -
                                            new Date(a.collected_at).getTime(),
                                    )
                                    .slice(0, 20)
                                    .map((metric) => (
                                        <div key={metric.id} className="list-item">
                                            <div className="list-item-title">
                                                {formatDate(metric.collected_at)}
                                            </div>
                                            <div className="list-item-meta">
                                                CPU: {metric.cpu_usage.toFixed(1)}% · RAM:{" "}
                                                {metric.memory_usage.toFixed(1)}% · Uptime:{" "}
                                                {formatUptime(metric.uptime_seconds)}
                                            </div>
                                        </div>
                                    ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}
