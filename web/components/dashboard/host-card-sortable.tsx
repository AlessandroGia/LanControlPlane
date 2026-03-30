"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

import { HostCard } from "@/components/dashboard/host-card";
import type { Agent, Host, HostLatestMetric } from "@/lib/types";

type HostCardSortableProps = {
    host: Host;
    agent?: Agent;
    latestMetric?: HostLatestMetric;
    onWake?: (hostName: string) => void;
    onShutdown?: (hostName: string) => void;
    onReboot?: (hostName: string) => void;
    actionsDisabled?: boolean;
    pendingCommand?: "wake" | "shutdown" | "reboot";
};

export function HostCardSortable({
    host,
    agent,
    latestMetric,
    onWake,
    onShutdown,
    onReboot,
    actionsDisabled,
    pendingCommand,
}: HostCardSortableProps) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({
        id: host.name,
    });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={isDragging ? "host-card-sortable dragging" : "host-card-sortable"}
        >
            <div className="host-card-drag-handle" {...attributes} {...listeners} aria-label={`Drag ${host.name}`}>
                ⋮⋮
            </div>

            <HostCard
                host={host}
                agent={agent}
                latestMetric={latestMetric}
                onWake={onWake}
                onShutdown={onShutdown}
                onReboot={onReboot}
                actionsDisabled={actionsDisabled}
                pendingCommand={pendingCommand}
            />
        </div>
    );
}
