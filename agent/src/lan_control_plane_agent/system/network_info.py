from __future__ import annotations

import socket
from typing import Final

import psutil

AF_LINK: Final[int] = getattr(psutil, "AF_LINK", object())


def get_primary_ip_address() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def get_mac_address() -> str | None:
    primary_ip = get_primary_ip_address()
    if primary_ip is None:
        return None

    addrs = psutil.net_if_addrs()

    for interface_name, interface_addrs in addrs.items():
        has_primary_ip = False
        mac_address = None

        for addr in interface_addrs:
            if addr.family == socket.AF_INET and addr.address == primary_ip:
                has_primary_ip = True

            if addr.family == AF_LINK:
                mac_address = addr.address

        if has_primary_ip and mac_address:
            return mac_address

    return None
