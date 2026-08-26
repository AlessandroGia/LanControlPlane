from fastapi import APIRouter, Depends

from lan_control_plane_server.api.deps import get_current_user_from_session
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.schemas.metric import HostLatestMetricRead
from lan_control_plane_server.services.metric_service import HostMetricService

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    dependencies=[Depends(get_current_user_from_session)],
)


@router.get("/latest", response_model=list[HostLatestMetricRead])
def get_latest_metrics() -> list[HostLatestMetricRead]:
    session = SessionLocal()
    try:
        metric_service = HostMetricService(session)
        rows = metric_service.get_latest_metrics_for_all_hosts()

        return [
            HostLatestMetricRead(
                host_id=host.id,
                host_name=host.name,
                cpu_usage=metric.cpu_usage,
                memory_usage=metric.memory_usage,
                uptime_seconds=metric.uptime_seconds,
                collected_at=metric.collected_at,
            )
            for host, metric in rows
        ]
    finally:
        session.close()
