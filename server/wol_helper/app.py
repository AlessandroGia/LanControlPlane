from __future__ import annotations

import logging
import socket

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("lan_control_plane_wol_helper")

app = FastAPI()


class WakeRequest(BaseModel):
    mac_address: str
    broadcast_ip: str = "10.10.10.255"
    port: int = 9


def normalize_mac_address(mac_address: str) -> str:
    normalized = mac_address.strip().lower().replace("-", ":")
    parts = normalized.split(":")

    if len(parts) != 6:
        raise ValueError(f"Invalid MAC address: {mac_address}")

    if any(len(part) != 2 for part in parts):
        raise ValueError(f"Invalid MAC address: {mac_address}")

    try:
        bytes.fromhex("".join(parts))
    except ValueError as exc:
        raise ValueError(f"Invalid MAC address: {mac_address}") from exc

    return ":".join(parts)


def send_magic_packet(mac_address: str, broadcast_ip: str, port: int) -> None:
    normalized = normalize_mac_address(mac_address)
    mac_bytes = bytes.fromhex(normalized.replace(":", ""))
    packet = b"\xff" * 6 + mac_bytes * 16

    LOGGER.info(
        "Host-side WOL send mac=%s broadcast_ip=%s port=%s",
        normalized,
        broadcast_ip,
        port,
    )

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (broadcast_ip, port))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/wake")
def wake(request: WakeRequest) -> dict[str, str]:
    try:
        send_magic_packet(
            mac_address=request.mac_address,
            broadcast_ip=request.broadcast_ip,
            port=request.port,
        )
    except Exception as exc:
        LOGGER.exception("WOL helper failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"status": "ok", "message": "Magic packet sent"}
