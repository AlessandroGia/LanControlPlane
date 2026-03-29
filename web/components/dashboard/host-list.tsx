import type { Agent, Host, HostLatestMetric } from "@/lib/types";
import { HostCard } from "./host-card";

type HostListProps = {
  hosts: Host[];
  agents: Agent[];
  latestMetrics: HostLatestMetric[];
  onWake?: (hostName: string) => void;
  onShutdown?: (hostName: string) => void;
  onReboot?: (hostName: string) => void;
  actionsDisabled?: boolean;
  pendingCommands?: Record<string, "wake" | "shutdown" | "reboot" | undefined>;
};

export function HostList({
  hosts,
  agents,
  latestMetrics,
  onWake,
  onShutdown,
  onReboot,
  actionsDisabled = false,
  pendingCommands = {},
}: HostListProps) {
  const agentMap = new Map(agents.map((agent) => [agent.host_name, agent]));
  const metricMap = new Map(latestMetrics.map((metric) => [metric.host_name, metric]));

  return (
    <div className="panel">
      <h2>Hosts</h2>
      <div className="host-list">
        {hosts.map((host) => (
          <HostCard
            key={host.id}
            host={host}
            agent={agentMap.get(host.name)}
            latestMetric={metricMap.get(host.name)}
            onWake={onWake}
            onShutdown={onShutdown}
            onReboot={onReboot}
            actionsDisabled={actionsDisabled}
            pendingCommand={pendingCommands[host.name]}
          />
        ))}
      </div>
    </div>
  );
}
