from sqlalchemy import select, update
from sqlalchemy.orm import Session

from lan_control_plane_server.db.models import Host


class HostRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self) -> list[Host]:
        statement = select(Host).order_by(Host.name)
        return list(self.session.scalars(statement).all())

    def get_by_id(self, host_id: str) -> Host | None:
        statement = select(Host).where(Host.id == host_id)
        return self.session.scalar(statement)

    def get_by_name(self, name: str) -> Host | None:
        statement = select(Host).where(Host.name == name)
        return self.session.scalar(statement)

    def mark_managed_hosts_offline(self) -> None:
        statement = (
            update(Host)
            .where(
                Host.is_managed.is_(True),
                Host.state.in_(["online", "shutting_down"]),
            )
            .values(state="offline")
        )
        self.session.execute(statement)
        self.session.commit()

    def create_managed_host(
        self,
        *,
        name: str,
        hostname: str,
        ip_address: str | None,
        state: str,
    ) -> Host:
        host = Host(
            name=name,
            hostname=hostname,
            ip_address=ip_address,
            state=state,
            is_managed=True,
        )
        self.session.add(host)
        self.session.commit()
        self.session.refresh(host)
        return host

    def update_state(self, host: Host, state: str) -> Host:
        host.state = state
        self.session.add(host)
        self.session.commit()
        self.session.refresh(host)
        return host

    def update_registration_info(
        self,
        host: Host,
        *,
        hostname: str,
        ip_address: str | None,
        state: str,
    ) -> Host:
        host.hostname = hostname
        if ip_address is not None:
            host.ip_address = ip_address
        host.state = state
        self.session.add(host)
        self.session.commit()
        self.session.refresh(host)
        return host

    def update_network_info(
        self,
        host: Host,
        *,
        ip_address: str | None = None,
        mac_address: str | None = None,
    ) -> Host:
        host.ip_address = ip_address
        host.mac_address = mac_address
        self.session.add(host)
        self.session.commit()
        self.session.refresh(host)
        return host
