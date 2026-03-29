from lan_control_plane_server.db.models import Job
from lan_control_plane_server.repositories.job_repository import JobRepository
from sqlalchemy.orm import Session


class JobService:
    def __init__(self, session: Session) -> None:
        self.job_repository = JobRepository(session)

    def create_job(
        self,
        *,
        host_id: str,
        command: str,
        requested_by: str,
    ) -> Job:
        return self.job_repository.create(
            host_id=host_id,
            command=command,
            requested_by=requested_by,
        )

    def get_job(self, job_id: str) -> Job | None:
        return self.job_repository.get_by_id(job_id)

    def get_jobs(self) -> list[Job]:
        return self.job_repository.get_all()

    def mark_job_running(self, job_id: str) -> Job | None:
        job = self.job_repository.get_by_id(job_id)
        if job is None:
            return None
        return self.job_repository.mark_running(job)

    def mark_job_completed(self, job_id: str, result_message: str) -> Job | None:
        job = self.job_repository.get_by_id(job_id)
        if job is None:
            return None
        return self.job_repository.mark_completed(job, result_message)

    def mark_job_failed(self, job_id: str, result_message: str) -> Job | None:
        job = self.job_repository.get_by_id(job_id)
        if job is None:
            return None
        return self.job_repository.mark_failed(job, result_message)
