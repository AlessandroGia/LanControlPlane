from lan_control_plane_server.db.models import Host, HostMetric
from lan_control_plane_server.repositories.host_metric_repository import HostMetricRepository
from sqlalchemy.orm import Session


class HostMetricService:
    def __init__(self, session: Session) -> None:
        self.host_metric_repository = HostMetricRepository(session)

    def record_heartbeat_metrics(
        self,
        *,
        host_id: str,
        cpu_usage: float,
        memory_usage: float,
        uptime_seconds: int,
    ) -> HostMetric:
        return self.host_metric_repository.create(
            host_id=host_id,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            uptime_seconds=uptime_seconds,
        )

    def get_metrics_for_host(self, *, host: Host, limit: int | None = None) -> list[HostMetric]:
        return self.host_metric_repository.get_for_host(host.id, limit=limit)

    def get_latest_metrics_for_all_hosts(self) -> list[tuple[Host, HostMetric]]:
        return self.host_metric_repository.get_latest_for_all_hosts()

