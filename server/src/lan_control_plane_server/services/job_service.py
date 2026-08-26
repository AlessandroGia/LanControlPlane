from sqlalchemy.orm import Session

from lan_control_plane_server.db.models import Job
from lan_control_plane_server.repositories.job_repository import JobRepository


class JobService:
    def __init__(self, session: Session) -> None:
        self.job_repository = JobRepository(session)

    def create_job(
        self,
        *,
        host_id: str,
        request_id: str | None = None,
        command: str,
        requested_by: str,
    ) -> Job:
        return self.job_repository.create(
            host_id=host_id,
            request_id=request_id,
            command=command,
            requested_by=requested_by,
        )

    def get_job(self, job_id: str) -> Job | None:
        return self.job_repository.get_by_id(job_id)

    def get_job_by_request_id(self, request_id: str) -> Job | None:
        return self.job_repository.get_by_request_id(request_id)

    def get_jobs(self, *, limit: int = 100) -> list[Job]:
        return self.job_repository.get_all(limit=limit)

    def mark_job_running(self, job_id: str, *, expected_host_id: str | None = None) -> Job | None:
        job = self.job_repository.get_by_id(job_id)
        if job is None or (expected_host_id is not None and job.host_id != expected_host_id):
            return None
        if job.status != "pending":
            return None
        return self.job_repository.mark_running(job)

    def mark_job_completed(
        self,
        job_id: str,
        result_message: str,
        *,
        expected_host_id: str | None = None,
    ) -> Job | None:
        job = self.job_repository.get_by_id(job_id)
        if job is None or (expected_host_id is not None and job.host_id != expected_host_id):
            return None
        if job.status not in {"pending", "running"}:
            return None
        return self.job_repository.mark_completed(job, result_message)

    def mark_job_failed(
        self,
        job_id: str,
        result_message: str,
        *,
        expected_host_id: str | None = None,
    ) -> Job | None:
        job = self.job_repository.get_by_id(job_id)
        if job is None or (expected_host_id is not None and job.host_id != expected_host_id):
            return None
        if job.status not in {"pending", "running"}:
            return None
        return self.job_repository.mark_failed(job, result_message)
