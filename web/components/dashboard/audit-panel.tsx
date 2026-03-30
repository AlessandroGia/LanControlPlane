"use client";

import { formatRelativeTime } from "@/lib/time";
import type { AuditLog } from "@/lib/types";

type AuditPanelProps = {
  logs: AuditLog[];
};

function buildAuditDescription(log: AuditLog): string {
  const actor = log.actor_id ?? log.actor_type;
  const target = log.target_id ? `${log.target_type} ${log.target_id}` : log.target_type;

  return `${actor} → ${log.action}${target ? ` → ${target}` : ""}`;
}

export function AuditPanel({ logs }: AuditPanelProps) {
  const sortedLogs = [...logs]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
    .slice(0, 10);

  return (
    <div className="panel">
      <div className="panel-header-row">
        <h2>Audit logs</h2>
      </div>

      {sortedLogs.length === 0 ? (
        <div className="panel-empty-state">No audit logs yet.</div>
      ) : (
        <div className="activity-list">
          {sortedLogs.map((log) => (
            <div key={log.id} className="activity-item">
              <div className="activity-item-top">
                <div className="activity-item-title">
                  <strong>{log.action}</strong>
                </div>

                <div className="activity-item-time">
                  {formatRelativeTime(log.created_at)}
                </div>
              </div>

              <div className="activity-item-message">
                {buildAuditDescription(log)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
