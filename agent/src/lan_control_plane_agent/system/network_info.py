from __future__ import annotations

import socket
import uuid


def get_primary_ip_address() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


def get_mac_address() -> str | None:
    mac = uuid.getnode()

    # Se l'ottavo bit del primo byte è 1, potrebbe essere un MAC random/locally administered
    first_byte = (mac >> 40) & 0xFF
    if first_byte & 0x02:
        # non blocchiamo tutto, lo restituiamo comunque
        pass

    mac_str = ":".join(f"{(mac >> offset) & 0xFF:02X}" for offset in range(40, -1, -8))
    return mac_str
