from sqlalchemy.orm import Session

from lan_control_plane_server.db.models import Host
from lan_control_plane_server.services.host_service import HostService


def test_restart_reconciliation_clears_transient_host_states(db_session: Session) -> None:
    hosts = [
        Host(name="online-host", hostname="online-host", state="online", is_managed=True),
        Host(name="waking-host", hostname="waking-host", state="waking", is_managed=True),
        Host(
            name="shutting-down-host",
            hostname="shutting-down-host",
            state="shutting_down",
            is_managed=True,
        ),
        Host(name="offline-host", hostname="offline-host", state="offline", is_managed=True),
        Host(name="unmanaged-host", hostname="unmanaged-host", state="waking", is_managed=False),
    ]
    db_session.add_all(hosts)
    db_session.commit()

    HostService(db_session).reconcile_after_server_restart()

    states = {host.name: host.state for host in db_session.query(Host).all()}
    assert states == {
        "online-host": "offline",
        "waking-host": "offline",
        "shutting-down-host": "offline",
        "offline-host": "offline",
        "unmanaged-host": "waking",
    }
