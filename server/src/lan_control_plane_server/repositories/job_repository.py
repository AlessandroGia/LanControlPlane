from datetime import UTC, datetime

from lan_control_plane_server.db.models import Job
from sqlalchemy import select
from sqlalchemy.orm import Session


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        host_id: str,
        command: str,
        requested_by: str,
    ) -> Job:
        job = Job(
            host_id=host_id,
            command=command,
            status="pending",
            requested_by=requested_by,
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_by_id(self, job_id: str) -> Job | None:
        statement = select(Job).where(Job.id == job_id)
        return self.session.scalar(statement)

    def get_all(self) -> list[Job]:
        statement = select(Job).order_by(Job.requested_at.desc())
        return list(self.session.scalars(statement).all())

    def mark_running(self, job: Job) -> Job:
        job.status = "running"
        job.started_at = datetime.now(UTC)
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def mark_completed(self, job: Job, result_message: str) -> Job:
        job.status = "completed"
        job.finished_at = datetime.now(UTC)
        job.result_message = result_message
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def mark_failed(self, job: Job, result_message: str) -> Job:
        job.status = "failed"
        job.finished_at = datetime.now(UTC)
        job.result_message = result_message
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
