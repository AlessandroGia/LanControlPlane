from __future__ import annotations

import logging

import httpx

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
        LOGGER.info(
            "Requesting host-side WOL for MAC=%s broadcast_ip=%s port=%s",
            mac_address,
            self.broadcast_ip,
            self.port,
        )

        response = httpx.post(
            f"{self.helper_base_url}/wake",
            json={
                "mac_address": mac_address,
                "broadcast_ip": self.broadcast_ip,
                "port": self.port,
            },
            timeout=5.0,
        )
        response.raise_for_status()
