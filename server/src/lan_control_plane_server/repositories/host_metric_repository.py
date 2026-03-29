from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from lan_control_plane_server.db.models import Host, HostMetric


class HostMetricRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        host_id: str,
        cpu_usage: float,
        memory_usage: float,
        uptime_seconds: int,
        collected_at: datetime | None = None,
    ) -> HostMetric:
        metric = HostMetric(
            host_id=host_id,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            uptime_seconds=uptime_seconds,
        )

        if collected_at is not None:
            metric.collected_at = collected_at

        self.session.add(metric)
        self.session.commit()
        self.session.refresh(metric)
        return metric

    def get_for_host(self, host_id: str, *, limit: int | None = None) -> list[HostMetric]:
        statement = (
            select(HostMetric)
            .where(HostMetric.host_id == host_id)
            .order_by(desc(HostMetric.collected_at))
        )

        if limit is not None:
            statement = statement.limit(limit)

        return list(self.session.scalars(statement).all())

    def get_latest_for_host(self, host_id: str) -> HostMetric | None:
        statement = (
            select(HostMetric)
            .where(HostMetric.host_id == host_id)
            .order_by(desc(HostMetric.collected_at))
            .limit(1)
        )
        return self.session.scalar(statement)

    def get_latest_for_all_hosts(self) -> list[tuple[Host, HostMetric]]:
        hosts = list(self.session.scalars(select(Host)).all())
        result: list[tuple[Host, HostMetric]] = []

        for host in hosts:
            latest = self.get_latest_for_host(host.id)
            if latest is not None:
                result.append((host, latest))

        return result
