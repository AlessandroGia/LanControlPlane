from __future__ import annotations

import logging
import socket
import subprocess

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("lan_control_plane_wol_helper")

app = FastAPI()


class WakeRequest(BaseModel):
    mac_address: str
    broadcast_ip: str = "10.10.10.255"
    port: int = 9


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/wake")
def wake(request: WakeRequest) -> dict[str, str]:
    LOGGER.info(
        "Sending host-side WOL packet mac=%s broadcast_ip=%s port=%s",
        request.mac_address,
        request.broadcast_ip,
        request.port,
    )

    try:
        subprocess.run(
            [
                "/usr/bin/wakeonlan",
                "-i",
                request.broadcast_ip,
                "-p",
                str(request.port),
                request.mac_address,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or str(exc)
        LOGGER.exception("WOL helper failed: %s", detail)
        raise HTTPException(status_code=500, detail=detail) from exc

    return {"status": "ok", "message": "Magic packet sent"}
