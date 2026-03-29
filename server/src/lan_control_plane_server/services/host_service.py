from lan_control_plane_server.db.models import Host
from lan_control_plane_server.repositories.host_repository import HostRepository
from lan_control_plane_shared.enums.host_state import HostState
from lan_control_plane_shared.protocol.server_messages import HostSnapshotItem
from sqlalchemy.orm import Session


class HostService:
    def __init__(self, session: Session) -> None:
        self.host_repository = HostRepository(session)

    def ensure_managed_host(
        self,
        *,
        name: str,
        hostname: str,
        ip_address: str | None,
    ) -> Host:
        existing = self.host_repository.get_by_name(name)
        if existing is None:
            return self.host_repository.create_managed_host(
                name=name,
                hostname=hostname,
                ip_address=ip_address,
                state=HostState.ONLINE.value,
            )

        return self.host_repository.update_state(existing, HostState.ONLINE.value)

    def mark_host_offline(self, name: str) -> None:
        host = self.host_repository.get_by_name(name)
        if host is None:
            return

        self.host_repository.update_state(host, HostState.OFFLINE.value)

    def mark_host_waking(self, name: str) -> Host | None:
        host = self.host_repository.get_by_name(name)
        if host is None:
            return None

        return self.host_repository.update_state(host, HostState.WAKING.value)

    def get_host_by_name(self, name: str) -> Host | None:
        return self.host_repository.get_by_name(name)

    def get_host_by_id(self, host_id: str) -> Host | None:
        return self.host_repository.get_by_id(host_id)

    def get_hosts(self) -> list[Host]:
        return self.host_repository.get_all()

    def update_host_network_info(
        self,
        *,
        name: str,
        ip_address: str | None,
        mac_address: str | None,
    ) -> Host | None:
        host = self.host_repository.get_by_name(name)
        if host is None:
            return None

        return self.host_repository.update_network_info(
            host,
            ip_address=ip_address,
            mac_address=mac_address,
        )

    def get_hosts_snapshot(self) -> list[HostSnapshotItem]:
        hosts = self.host_repository.get_all()
        return [
            HostSnapshotItem(
                id=host.name,
                name=host.name,
                state=HostState(host.state),
                is_managed=host.is_managed,
            )
            for host in hosts
        ]
