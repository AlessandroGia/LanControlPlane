from datetime import datetime

from sqlalchemy import and_, delete, desc, func, select
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

    def prune_for_host(self, host_id: str, *, before: datetime) -> None:
        statement = delete(HostMetric).where(
            HostMetric.host_id == host_id,
            HostMetric.collected_at < before,
        )
        self.session.execute(statement)

    def get_for_host(self, host_id: str, *, limit: int | None = None) -> list[HostMetric]:
        statement = select(HostMetric).where(HostMetric.host_id == host_id).order_by(desc(HostMetric.collected_at))

        if limit is not None:
            statement = statement.limit(limit)

        return list(self.session.scalars(statement).all())

    def get_latest_for_host(self, host_id: str) -> HostMetric | None:
        statement = (
            select(HostMetric).where(HostMetric.host_id == host_id).order_by(desc(HostMetric.collected_at)).limit(1)
        )
        return self.session.scalar(statement)

    def get_latest_for_all_hosts(self) -> list[tuple[Host, HostMetric]]:
        latest_by_host = (
            select(
                HostMetric.host_id.label("host_id"),
                func.max(HostMetric.collected_at).label("collected_at"),
            )
            .group_by(HostMetric.host_id)
            .subquery()
        )
        statement = (
            select(Host, HostMetric)
            .join(latest_by_host, latest_by_host.c.host_id == Host.id)
            .join(
                HostMetric,
                and_(
                    HostMetric.host_id == latest_by_host.c.host_id,
                    HostMetric.collected_at == latest_by_host.c.collected_at,
                ),
            )
            .order_by(Host.name)
        )
        return [(host, metric) for host, metric in self.session.execute(statement).all()]
