import { LogoutButton } from "@/components/auth/logout-button";
import { DashboardClient } from "@/components/dashboard/dashboard-client";
import { getAgents, getAuditLogs, getHosts, getJobs, getLatestMetrics, getMe } from "@/lib/api";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

function buildCookieHeader(
  cookieStore: Awaited<ReturnType<typeof cookies>>,
): string | undefined {
  const all = cookieStore.getAll();
  if (all.length === 0) {
    return undefined;
  }

  return all.map((cookie) => `${cookie.name}=${cookie.value}`).join("; ");
}

export default async function HomePage() {
  const cookieStore = await cookies();
  const cookieHeader = buildCookieHeader(cookieStore);

  if (!cookieHeader) {
    redirect("/login");
  }

  try {
    await getMe(cookieHeader);
  } catch {
    redirect("/login");
  }

  const [hosts, jobs, agents, auditLogs, latestMetrics] = await Promise.all([
    getHosts(cookieHeader),
    getJobs(cookieHeader),
    getAgents(cookieHeader),
    getAuditLogs(cookieHeader),
    getLatestMetrics(cookieHeader),
  ]);

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
        hosts={hosts}
        jobs={jobs}
        agents={agents}
        auditLogs={auditLogs}
        latestMetrics={latestMetrics}
      />
    </main>
  );
}
