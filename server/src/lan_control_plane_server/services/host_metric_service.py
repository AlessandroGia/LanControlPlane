from sqlalchemy.orm import Session

from lan_control_plane_server.db.models import Host, HostMetric
from lan_control_plane_server.repositories.host_metric_repository import HostMetricRepository


class HostMetricService:
    def __init__(self, session: Session) -> None:
        self.host_metric_repository = HostMetricRepository(session)

    def get_latest_metrics_for_all_hosts(self) -> list[tuple[Host, HostMetric]]:
        return self.host_metric_repository.get_latest_for_all_hosts()
