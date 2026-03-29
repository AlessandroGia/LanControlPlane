from lan_control_plane_server.db.models import Host


def create_host(
    session,
    *,
    name: str = "desktop-casa",
    hostname: str = "desktop-casa",
    state: str = "online",
    ip_address: str | None = None,
    mac_address: str | None = None,
    is_managed: bool = True,
) -> Host:
    host = Host(
        name=name,
        hostname=hostname,
        state=state,
        ip_address=ip_address,
        mac_address=mac_address,
        is_managed=is_managed,
    )
    session.add(host)
    session.commit()
    session.refresh(host)
    return host
