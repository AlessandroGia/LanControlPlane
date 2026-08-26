import asyncio
import getpass
import json
import os
from typing import Any
from uuid import uuid4

import httpx
import websockets

SERVER_HTTP_URL = os.getenv("SERVER_HTTP_URL", "http://localhost:8000")
SERVER_WS_CLIENT_URL = os.getenv("SERVER_WS_CLIENT_URL", "ws://localhost:8000/ws/client")


async def receive_loop(websocket: websockets.ClientConnection) -> None:
    while True:
        message = await websocket.recv()
        try:
            payload: Any = json.loads(message)
        except json.JSONDecodeError:
            print(f"[RECV] raw: {message}")
            continue
        print(json.dumps(payload, indent=2, ensure_ascii=False))


async def input_loop(websocket: websockets.ClientConnection) -> None:
    loop = asyncio.get_running_loop()
    while True:
        raw = await loop.run_in_executor(
            None,
            input,
            "\nCommand (hosts / shutdown <host> / reboot <host> / wake <host> / quit): ",
        )
        raw = raw.strip()
        if not raw:
            continue
        if raw == "quit":
            await websocket.close()
            return
        if raw == "hosts":
            await websocket.send(json.dumps({"type": "get_hosts"}))
            continue

        parts = raw.split(maxsplit=1)
        if len(parts) != 2 or parts[0] not in {"shutdown", "reboot", "wake"}:
            print("Invalid command format.")
            continue

        command, host_id = parts
        await websocket.send(
            json.dumps(
                {
                    "type": "command_request",
                    "request_id": str(uuid4()),
                    "host_id": host_id,
                    "command": command,
                }
            )
        )


async def create_session_cookie() -> str:
    username = os.getenv("LCP_USERNAME", "admin")
    password = os.getenv("LCP_PASSWORD") or getpass.getpass("Password: ")
    async with httpx.AsyncClient(base_url=SERVER_HTTP_URL) as client:
        response = await client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )
        response.raise_for_status()
        token = client.cookies.get("lcp_session")
        if token is None:
            raise RuntimeError("Login response did not set a session cookie")
        return token


async def main() -> None:
    session_token = await create_session_cookie()
    async with websockets.connect(
        SERVER_WS_CLIENT_URL,
        additional_headers={"Cookie": f"lcp_session={session_token}"},
    ) as websocket:
        await asyncio.gather(receive_loop(websocket), input_loop(websocket))


if __name__ == "__main__":
    asyncio.run(main())
