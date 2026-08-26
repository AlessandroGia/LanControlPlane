import { LogoutButton } from "@/components/auth/logout-button";
import { DashboardClient } from "@/components/dashboard/dashboard-client";
import { getAgents, getAuditLogs, getHosts, getJobs, getLatestMetrics, getMe } from "@/lib/api";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

function buildCookieHeader(
  cookieStore: Awaited<ReturnType<typeof cookies>>,
): string | undefined {
  const sessionCookie = cookieStore.get("lcp_session");
  if (!sessionCookie) {
    return undefined;
  }

  return `${sessionCookie.name}=${sessionCookie.value}`;
}

export default async function HomePage() {
  const cookieStore = await cookies();
  const cookieHeader = buildCookieHeader(cookieStore);

  if (!cookieHeader) {
    redirect("/login");
  }

  let currentUser: Awaited<ReturnType<typeof getMe>>;
  try {
    currentUser = await getMe(cookieHeader);
  } catch {
    redirect("/login");
  }

  const results = await Promise.allSettled([
    getHosts(cookieHeader),
    getJobs(cookieHeader),
    getAgents(cookieHeader),
    getAuditLogs(cookieHeader),
    getLatestMetrics(cookieHeader),
  ]);
  const [hostsResult, jobsResult, agentsResult, auditLogsResult, metricsResult] = results;

  const hosts = hostsResult.status === "fulfilled" ? hostsResult.value : [];
  const jobs = jobsResult.status === "fulfilled" ? jobsResult.value : [];
  const agents = agentsResult.status === "fulfilled" ? agentsResult.value : [];
  const auditLogs = auditLogsResult.status === "fulfilled" ? auditLogsResult.value : [];
  const latestMetrics = metricsResult.status === "fulfilled" ? metricsResult.value : [];
  const initialError = results.some((result) => result.status === "rejected")
    ? "Some dashboard data could not be loaded. Retrying automatically."
    : null;

  return (
    <main className="container">
      <div className="page-header">
        <div>
          <h1 className="page-title">LAN Control Plane</h1>
          <p className="page-subtitle">
            Live LAN host dashboard with jobs, audit visibility, and metrics.
          </p>
        </div>

        <LogoutButton />
      </div>

      <DashboardClient
        currentUser={currentUser}
        initialError={initialError}
        hosts={hosts}
        jobs={jobs}
        agents={agents}
        auditLogs={auditLogs}
        latestMetrics={latestMetrics}
      />
    </main>
  );
}
