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
        transform: CSS.Transform.toString(
            transform
                ? {
                    ...transform,
                    scaleX: isDragging ? 1.01 : 1,
                    scaleY: isDragging ? 1.01 : 1,
                }
                : null,
        ),
        transition: transition ?? "transform 220ms cubic-bezier(0.22, 1, 0.36, 1)",
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`host-card-sortable${isDragging ? " dragging" : ""}`}
        >
            <HostCard
                host={host}
                agent={agent}
                latestMetric={latestMetric}
                onWake={onWake}
                onShutdown={onShutdown}
                onReboot={onReboot}
                actionsDisabled={actionsDisabled}
                pendingCommand={pendingCommand}
                dragHandleProps={{
                    attributes,
                    listeners,
                }}
            />
        </div>
    );
}
