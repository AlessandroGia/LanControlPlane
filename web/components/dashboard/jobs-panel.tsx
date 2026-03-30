"use client";

import { formatRelativeTime } from "@/lib/time";
import type { Job } from "@/lib/types";

type JobsPanelProps = {
  jobs: Job[];
};

const jobStatusLabelMap: Record<Job["status"], string> = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
};

export function JobsPanel({ jobs }: JobsPanelProps) {
  const sortedJobs = [...jobs]
    .sort(
      (a, b) =>
        new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime(),
    )
    .slice(0, 8);

  if (sortedJobs.length === 0) {
    return <div className="panel-empty-state">No jobs yet.</div>;
  }

  return (
    <div className="activity-list">
      {sortedJobs.map((job) => (
        <div key={job.id} className="activity-item">
          <div className="activity-item-top">
            <div className="activity-item-title">
              <span className={`status-pill ${job.status}`}>
                {jobStatusLabelMap[job.status]}
              </span>
              <span>
                {job.command} on <strong>{job.host_id}</strong>
              </span>
            </div>

            <div className="activity-item-time">
              {formatRelativeTime(job.requested_at)}
            </div>
          </div>

          {job.result_message ? (
            <div className="activity-item-message">{job.result_message}</div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
