"use client";

import { formatRelativeTime, isOlderThan } from "@/lib/time";
import type { Agent, Host, HostLatestMetric } from "@/lib/types";
import { useHydrated } from "@/lib/use-hydrated";
import type { DraggableAttributes } from "@dnd-kit/core";
import type { SyntheticListenerMap } from "@dnd-kit/core/dist/hooks/utilities";
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
  dragHandleProps?: {
    attributes: DraggableAttributes;
    listeners: SyntheticListenerMap | undefined;
  };
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

function MetricTile({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="host-metric-tile">
      <div className="host-metric-label">{label}</div>
      <div className="host-metric-value">{value}</div>
    </div>
  );
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
  dragHandleProps,
}: HostCardProps) {
  const hydrated = useHydrated();
  const hostBusy = Boolean(pendingCommand);

  const metricStale =
    hydrated && latestMetric ? isOlderThan(latestMetric.collected_at, 120) : false;

  const agentLastSeenStale =
    hydrated && agent?.last_seen_at ? isOlderThan(agent.last_seen_at, 60) : false;

  const isOffline = host.state === "offline";
  const isOnline = host.state === "online";
  const isWaking = host.state === "waking";
  const isShuttingDown = host.state === "shutting_down";
  const isUnknown = host.state === "unknown";

  const wakeDisabled =
    actionsDisabled || hostBusy || isOnline || isWaking || isShuttingDown || isUnknown;

  const shutdownDisabled =
    actionsDisabled || hostBusy || isOffline || isWaking || isShuttingDown || isUnknown;

  const rebootDisabled =
    actionsDisabled || hostBusy || isOffline || isWaking || isShuttingDown || isUnknown;

  const secondaryStatus =
    agent?.last_seen_at && agentLastSeenStale
      ? hydrated
        ? `Agent stale · last seen ${formatRelativeTime(agent.last_seen_at)}`
        : "Agent stale"
      : !agentLastSeenStale && metricStale
        ? "Metrics stale"
        : null;

  return (
    <article className="host-card">
      <div
        className="host-card-header host-card-header-draggable"
        {...(dragHandleProps?.attributes ?? {})}
        {...(dragHandleProps?.listeners ?? {})}
      >
        <div className="host-card-title-wrap">
          <div className="host-name">
            <Link href={`/hosts/${host.name}`}>{host.name}</Link>
          </div>

          <div className="host-card-submeta">
            <span>IP: {host.ip_address ?? "—"}</span>
            <span>MAC: {host.mac_address ?? "—"}</span>
          </div>

          <div className="host-card-submeta">
            <span>
              Agent: {agent ? `${agent.version} · ${agent.enabled ? "enabled" : "disabled"}` : "—"}
            </span>
          </div>
        </div>

        <div className="host-card-status-wrap">
          <span className={`badge ${host.state}`}>{stateLabelMap[host.state]}</span>
        </div>
      </div>

      <div className="host-card-body">
        {latestMetric ? (
          <div className="host-metrics-grid">
            <MetricTile label="CPU" value={`${latestMetric.cpu_usage.toFixed(1)}%`} />
            <MetricTile label="RAM" value={`${latestMetric.memory_usage.toFixed(1)}%`} />
            <MetricTile label="Uptime" value={formatUptime(latestMetric.uptime_seconds)} />
          </div>
        ) : (
          <div className="host-empty-metrics">No metrics yet.</div>
        )}

        {secondaryStatus ? (
          <div className="host-card-secondary-status stale-text">{secondaryStatus}</div>
        ) : null}

        {hostBusy ? (
          <div className="host-card-secondary-status">
            Pending command: {pendingCommand}
          </div>
        ) : null}
      </div>

      <div className="host-card-actions">
        <div className="host-card-actions-left">
          <button
            className="host-action-button host-action-button-danger"
            disabled={shutdownDisabled}
            onClick={() => onShutdown?.(host.name)}
            title={shutdownDisabled ? "Shutdown is not available for this host state" : "Shutdown host"}
          >
            {pendingCommand === "shutdown" ? "Shutting down..." : "Shutdown"}
          </button>

          <button
            className="host-action-button host-action-button-danger"
            disabled={rebootDisabled}
            onClick={() => onReboot?.(host.name)}
            title={rebootDisabled ? "Reboot is not available for this host state" : "Reboot host"}
          >
            {pendingCommand === "reboot" ? "Rebooting..." : "Reboot"}
          </button>
        </div>

        <div className="host-card-actions-right">
          <button
            className="host-action-button host-action-button-primary"
            disabled={wakeDisabled}
            onClick={() => onWake?.(host.name)}
            title={wakeDisabled ? "Wake is not available for this host state" : "Wake host"}
          >
            {pendingCommand === "wake" ? "Waking..." : "Wake"}
          </button>
        </div>
      </div>
    </article>
  );
}
