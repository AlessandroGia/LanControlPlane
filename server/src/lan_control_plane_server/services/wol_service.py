import logging
import socket

LOGGER = logging.getLogger(__name__)

class WakeOnLanService:
    def send_magic_packet(self, mac_address: str, *, broadcast_ip: str = "255.255.255.255") -> None:
        normalized_mac = mac_address.replace(":", "").replace("-", "").strip().lower()

        if len(normalized_mac) != 12:
            raise ValueError("Invalid MAC address format")

        try:
            mac_bytes = bytes.fromhex(normalized_mac)
        except ValueError as exc:
            raise ValueError("Invalid MAC address format") from exc

        packet = b"\xff" * 6 + mac_bytes * 16

        LOGGER.info(
            "Sending WOL magic packet to MAC=%s broadcast_ip=%s port=%s",
            mac_address,
            broadcast_ip,
            9,
        )

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(packet, (broadcast_ip, 9))
