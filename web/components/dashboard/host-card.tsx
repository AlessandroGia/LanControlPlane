"use client";

import { formatRelativeTime, isOlderThan } from "@/lib/time";
import type { Agent, Host, HostLatestMetric } from "@/lib/types";
import { useHydrated } from "@/lib/use-hydrated";
import Link from "next/link";

type HostCardProps = {
  host: Host;
  agent?: Agent;
  latestMetric?: HostLatestMetric;
  onWake?: (hostName: string) => void;
  onShutdown?: (hostName: string) => void;
  onReboot?: (hostName: string) => void;
  actionsDisabled?: boolean;
  pendingCommand?: "wake" | "shutdown" | "reboot";
};

const stateLabelMap: Record<Host["state"], string> = {
  online: "Online",
  offline: "Offline",
  waking: "Waking",
  shutting_down: "Shutting down",
  unknown: "Unknown",
};

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

export function HostCard({
  host,
  agent,
  latestMetric,
  onWake,
  onShutdown,
  onReboot,
  actionsDisabled = false,
  pendingCommand,
}: HostCardProps) {
  const hydrated = useHydrated();
  const hostBusy = Boolean(pendingCommand);

  const metricStale =
    hydrated && latestMetric ? isOlderThan(latestMetric.collected_at, 120) : false;

  const agentLastSeenStale =
    hydrated && agent?.last_seen_at ? isOlderThan(agent.last_seen_at, 60) : false;

  return (
    <div className="host-card">
      <div className="host-card-top">
        <div>
          <div className="host-name">
            <Link href={`/hosts/${host.name}`}>{host.name}</Link>
          </div>

          <div className="host-meta">
            IP: {host.ip_address ?? "—"} · MAC: {host.mac_address ?? "—"}
          </div>

          {latestMetric ? (
            <div className="host-meta">
              CPU: {latestMetric.cpu_usage.toFixed(1)}% · RAM: {latestMetric.memory_usage.toFixed(1)}% · Uptime:{" "}
              {formatUptime(latestMetric.uptime_seconds)}
            </div>
          ) : (
            <div className="host-meta">Metrics: —</div>
          )}

          {agent?.last_seen_at && agentLastSeenStale ? (
            <div className="host-meta stale-text">
              {hydrated
                ? `Agent stale · last seen ${formatRelativeTime(agent.last_seen_at)}`
                : "Agent stale"}
            </div>
          ) : !agentLastSeenStale && metricStale ? (
            <div className="host-meta stale-text">Metrics stale</div>
          ) : null}

          <div className="host-meta">
            Agent: {agent ? `${agent.version} · ${agent.enabled ? "enabled" : "disabled"}` : "—"}
          </div>

          {hostBusy ? <div className="host-meta">Pending command: {pendingCommand}</div> : null}
        </div>

        <span className={`badge ${host.state}`}>{stateLabelMap[host.state]}</span>
      </div>

      <div className="host-actions">
        <button disabled={actionsDisabled || hostBusy} onClick={() => onWake?.(host.name)}>
          {pendingCommand === "wake" ? "Waking..." : "Wake"}
        </button>
        <button disabled={actionsDisabled || hostBusy} onClick={() => onShutdown?.(host.name)}>
          {pendingCommand === "shutdown" ? "Shutting down..." : "Shutdown"}
        </button>
        <button disabled={actionsDisabled || hostBusy} onClick={() => onReboot?.(host.name)}>
          {pendingCommand === "reboot" ? "Rebooting..." : "Reboot"}
        </button>
      </div>
    </div>
  );
}
