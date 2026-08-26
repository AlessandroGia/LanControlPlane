from __future__ import annotations

import logging
import os
import secrets
import socket
from ipaddress import IPv4Address

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("lan_control_plane_wol_helper")

app = FastAPI()
EXPECTED_TOKEN = os.getenv("WOL_HELPER_TOKEN", "")


class WakeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_default=True)

    mac_address: str
    broadcast_ip: IPv4Address = IPv4Address("255.255.255.255")
    port: int = Field(default=9, ge=1, le=65535)

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, value: str) -> str:
        return normalize_mac_address(value)


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
def wake(
    request: WakeRequest,
    x_wol_token: str | None = Header(default=None),
) -> dict[str, str]:
    if not EXPECTED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WOL helper token is not configured",
        )
    if x_wol_token is None or not secrets.compare_digest(x_wol_token, EXPECTED_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid WOL helper token",
        )

    try:
        send_magic_packet(
            mac_address=request.mac_address,
            broadcast_ip=str(request.broadcast_ip),
            port=request.port,
        )
    except Exception as exc:
        LOGGER.exception("WOL helper failed: %s", exc)
        raise HTTPException(status_code=500, detail="Unable to send magic packet") from exc

    return {"status": "ok", "message": "Magic packet sent"}
