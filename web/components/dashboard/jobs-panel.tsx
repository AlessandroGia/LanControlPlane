import type { Job } from "@/lib/types";

type JobsPanelProps = {
  jobs: Job[];
};

export function JobsPanel({ jobs }: JobsPanelProps) {
  return (
    <div className="panel">
      <h2>Recent jobs</h2>

      {jobs.length === 0 ? (
        <div className="list-item-meta">No jobs yet.</div>
      ) : (
        <div className="list">
          {jobs.slice(0, 10).map((job) => (
            <div key={job.id} className="list-item">
              <div className="list-item-title">
                {job.command} · {job.status}
              </div>
              <div className="list-item-meta">
                Host ID: {job.host_id} · Requested by: {job.requested_by}
              </div>
              {job.result_message ? (
                <div className="list-item-meta">{job.result_message}</div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
