import logging

import httpx
from lan_control_plane_server.utils.network import normalize_mac_address

LOGGER = logging.getLogger(__name__)

class WakeOnLanService:
    def __init__(
        self,
        *,
        helper_base_url: str,
        broadcast_ip: str,
        port: int,
    ) -> None:
        self.helper_base_url = helper_base_url.rstrip("/")
        self.broadcast_ip = broadcast_ip
        self.port = port

    def send_magic_packet(self, mac_address: str) -> None:
        normalized_mac_address = normalize_mac_address(mac_address)
        LOGGER.info(
            "Requesting host-side WOL for MAC=%s broadcast_ip=%s port=%s",
            normalized_mac_address,
            self.broadcast_ip,
            self.port,
        )

        response = httpx.post(
            f"{self.helper_base_url}/wake",
            json={
                "mac_address": normalized_mac_address,
                "broadcast_ip": self.broadcast_ip,
                "port": self.port,
            },
            timeout=5.0,
        )
        response.raise_for_status()
