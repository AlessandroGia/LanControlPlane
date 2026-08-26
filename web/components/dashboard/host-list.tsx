"use client";

import {
  closestCenter,
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useMemo, useState } from "react";

import { HostCardSortable } from "@/components/dashboard/host-card-sortable";
import type { Agent, Host, HostLatestMetric } from "@/lib/types";
import { useHydrated } from "@/lib/use-hydrated";

type HostListProps = {
  hosts: Host[];
  agents: Agent[];
  latestMetrics: HostLatestMetric[];
  onWake?: (hostName: string) => void;
  onShutdown?: (hostName: string) => void;
  onReboot?: (hostName: string) => void;
  onDelete?: (hostName: string) => void;
  canDelete?: boolean;
  actionsDisabled?: boolean;
  pendingCommands?: Record<string, "wake" | "shutdown" | "reboot" | undefined>;
};

const STORAGE_KEY = "lan-control-plane-host-order";

function loadStoredOrder(): string[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function saveStoredOrder(order: string[]): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(order));
}

function reconcileOrder(order: string[], hosts: Host[]): string[] {
  const hostIds = hosts.map((host) => host.name);
  const existing = order.filter((id) => hostIds.includes(id));
  const missing = hostIds.filter((id) => !existing.includes(id));
  return [...existing, ...missing];
}

export function HostList({
  hosts,
  agents,
  latestMetrics,
  onWake,
  onShutdown,
  onReboot,
  onDelete,
  canDelete = false,
  actionsDisabled = false,
  pendingCommands = {},
}: HostListProps) {
  const hydrated = useHydrated();
  const [preferredOrder, setPreferredOrder] = useState<string[] | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 10,
      },
    }),
  );

  const hostOrder = useMemo(
    () => reconcileOrder(preferredOrder ?? (hydrated ? loadStoredOrder() : []), hosts),
    [hosts, hydrated, preferredOrder],
  );

  const orderedHosts = useMemo(() => {
    const hostMap = new Map(hosts.map((host) => [host.name, host]));
    return hostOrder
      .map((id) => hostMap.get(id))
      .filter((host): host is Host => Boolean(host));
  }, [hostOrder, hosts]);

  function handleDragEnd(event: DragEndEvent): void {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    const oldIndex = hostOrder.indexOf(String(active.id));
    const newIndex = hostOrder.indexOf(String(over.id));

    if (oldIndex === -1 || newIndex === -1) {
      return;
    }

    const next = arrayMove(hostOrder, oldIndex, newIndex);
    saveStoredOrder(next);
    setPreferredOrder(next);
  }

  if (orderedHosts.length === 0) {
    return <div className="panel-empty-state">No hosts available.</div>;
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={orderedHosts.map((host) => host.name)} strategy={verticalListSortingStrategy}>
        <div className="host-list">
          {orderedHosts.map((host) => {
            const agent = agents.find((item) => item.host_name === host.name);
            const latestMetric = latestMetrics.find((item) => item.host_name === host.name);

            return (
              <HostCardSortable
                key={host.name}
                host={host}
                agent={agent}
                latestMetric={latestMetric}
                onWake={onWake}
                onShutdown={onShutdown}
                onReboot={onReboot}
                onDelete={onDelete}
                canDelete={canDelete}
                actionsDisabled={actionsDisabled}
                pendingCommand={pendingCommands[host.name]}
              />
            );
          })}
        </div>
      </SortableContext>
    </DndContext>
  );
}
