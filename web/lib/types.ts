export type HostState = "online" | "offline" | "waking" | "shutting_down" | "unknown";

export type JobStatus = "pending" | "running" | "completed" | "failed";

export interface Host {
  id: string;
  name: string;
  hostname: string;
  ip_address: string | null;
  mac_address: string | null;
  state: HostState;
  is_managed: boolean;
  created_at: string;
  updated_at: string;
}

export interface Job {
  id: string;
  host_id: string;
  command: string;
  status: JobStatus;
  requested_by: string;
  requested_at: string;
  started_at: string | null;
  finished_at: string | null;
  result_message: string | null;
}

export interface Agent {
  id: string;
  host_id: string;
  host_name: string;
  version: string;
  enabled: boolean;
  last_seen_at: string | null;
}

export interface AuditLog {
  id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  target_type: string;
  target_id: string;
  metadata_json: string | null;
  created_at: string;
}

export interface HostLatestMetric {
  host_id: string;
  host_name: string;
  cpu_usage: number;
  memory_usage: number;
  uptime_seconds: number;
  collected_at: string;
}

export interface HostMetricRead {
  id: string;
  host_id: string;
  cpu_usage: number;
  memory_usage: number;
  uptime_seconds: number;
  collected_at: string;
}
