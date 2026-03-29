import { config } from "./config";
import type {
  Agent,
  AuditLog,
  Host,
  HostLatestMetric,
  HostMetricRead,
  Job,
} from "./types";

function buildHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
  };
}

export async function getLatestMetrics(cookieHeader?: string): Promise<HostLatestMetric[]> {
  return fetchJson("/metrics/latest", {
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${config.internalApiBaseUrl}${path}`, {
    ...init,
    headers: {
      ...buildHeaders(),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }

  return (await response.json()) as T;
}

export async function getMe(cookieHeader?: string): Promise<{
  id: string;
  username: string;
  role: string;
}> {
  return fetchJson("/auth/me", {
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
}

export async function getHosts(cookieHeader?: string): Promise<Host[]> {
  return fetchJson("/hosts", {
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
}

export async function getJobs(cookieHeader?: string): Promise<Job[]> {
  return fetchJson("/jobs", {
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
}

export async function getAgents(cookieHeader?: string): Promise<Agent[]> {
  return fetchJson("/agents", {
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
}

export async function getAuditLogs(cookieHeader?: string): Promise<AuditLog[]> {
  return fetchJson("/audit-logs", {
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
}

export async function getHost(
  hostName: string,
  cookieHeader?: string,
): Promise<Host> {
  return fetchJson(`/hosts/${hostName}`, {
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
}

export async function getHostMetrics(
  hostName: string,
  cookieHeader?: string,
): Promise<HostMetricRead[]> {
  return fetchJson(`/hosts/${hostName}/metrics`, {
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
}
