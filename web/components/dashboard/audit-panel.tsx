import type { AuditLog } from "@/lib/types";

type AuditPanelProps = {
  logs: AuditLog[];
};

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

export function AuditPanel({ logs }: AuditPanelProps) {
  return (
    <div className="panel">
      <h2>Recent audit logs</h2>

      {logs.length === 0 ? (
        <div className="list-item-meta">No audit logs yet.</div>
      ) : (
        <div className="list">
          {logs.slice(0, 10).map((log) => (
            <div key={log.id} className="list-item">
              <div className="list-item-title">{log.action}</div>
              <div className="list-item-meta">
                {log.actor_type}:{log.actor_id} → {log.target_type}:{log.target_id}
              </div>
              <div className="list-item-meta">{formatDate(log.created_at)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
