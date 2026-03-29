from fastapi import APIRouter, Depends
from lan_control_plane_server.api.deps import require_api_key
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.schemas.job import JobRead
from lan_control_plane_server.services.job_service import JobService
from lan_control_plane_shared.enums.job_status import JobStatus
from lan_control_plane_server.api.deps import get_current_user_from_session
from lan_control_plane_server.db.models import User

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(get_current_user_from_session)],
)


@router.get("", response_model=list[JobRead])
async def get_jobs() -> list[JobRead]:
    session = SessionLocal()
    try:
        job_service = JobService(session)
        jobs = job_service.get_jobs()
        return [
            JobRead(
                id=job.id,
                host_id=job.host_id,
                command=job.command,
                status=JobStatus(job.status),
                requested_by=job.requested_by,
                requested_at=job.requested_at,
                started_at=job.started_at,
                finished_at=job.finished_at,
                result_message=job.result_message,
            )
            for job in jobs
        ]
    finally:
        session.close()
