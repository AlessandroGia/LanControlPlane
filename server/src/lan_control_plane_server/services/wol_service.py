import logging

import httpx

from lan_control_plane_server.utils.network import normalize_mac_address

LOGGER = logging.getLogger(__name__)


class WakeOnLanService:
    def __init__(
        self,
        *,
        helper_base_url: str,
        helper_token: str,
        broadcast_ip: str,
        port: int,
    ) -> None:
        self.helper_base_url = helper_base_url.rstrip("/")
        self.helper_token = helper_token
        self.broadcast_ip = broadcast_ip
        self.port = port

    async def send_magic_packet(self, mac_address: str) -> None:
        normalized_mac_address = normalize_mac_address(mac_address)
        LOGGER.info(
            "Requesting host-side WOL for MAC=%s broadcast_ip=%s port=%s",
            normalized_mac_address,
            self.broadcast_ip,
            self.port,
        )

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{self.helper_base_url}/wake",
                headers={"X-WOL-Token": self.helper_token},
                json={
                    "mac_address": normalized_mac_address,
                    "broadcast_ip": self.broadcast_ip,
                    "port": self.port,
                },
            )
        response.raise_for_status()
