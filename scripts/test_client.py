import asyncio
import json
import os
from typing import Any

import websockets

SERVER_WS_CLIENT_URL = os.getenv("SERVER_WS_CLIENT_URL", "ws://localhost:8000/ws/client")
CLIENT_TOKEN = os.getenv("CLIENT_TOKEN", "dev-client-token")


async def receive_loop(websocket: websockets.ClientConnection) -> None:
    while True:
        message = await websocket.recv()
        try:
            payload: Any = json.loads(message)
        except json.JSONDecodeError:
            print(f"[RECV] raw: {message}")
            continue

        print("[RECV]")
        print(json.dumps(payload, indent=2, ensure_ascii=False))


async def input_loop(websocket: websockets.ClientConnection) -> None:
    loop = asyncio.get_running_loop()

    while True:
        raw = await loop.run_in_executor(
            None,
            input,
            "\nComando (hosts / shutdown <host> / reboot <host> / wake <host> / quit): ",
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
        if len(parts) != 2:
            print("Formato non valido.")
            continue

        command, host_id = parts
        if command not in {"shutdown", "reboot", "wake"}:
            print("Comando non supportato.")
            continue

        payload = {
            "type": "command_request",
            "request_id": f"req-{command}-{host_id}",
            "host_id": host_id,
            "command": command,
        }
        await websocket.send(json.dumps(payload))


async def main() -> None:
    async with websockets.connect(SERVER_WS_CLIENT_URL) as websocket:
        initial_message = await websocket.recv()
        print("[RECV]")
        print(json.dumps(json.loads(initial_message), indent=2, ensure_ascii=False))

        auth_payload = {
            "type": "auth",
            "token": CLIENT_TOKEN,
        }
        await websocket.send(json.dumps(auth_payload))

        await asyncio.gather(
            receive_loop(websocket),
            input_loop(websocket),
        )


if __name__ == "__main__":
    asyncio.run(main())
