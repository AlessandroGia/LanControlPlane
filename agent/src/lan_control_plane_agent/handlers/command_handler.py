from __future__ import annotations

import asyncio

from lan_control_plane_agent.handlers.platform_commands import \
    get_platform_commands
from lan_control_plane_shared.enums.command import Command


async def handle_command(*, command: str, dry_run: bool) -> str:
    platform_commands = get_platform_commands()

    if command == Command.SHUTDOWN.value:
        command_args = platform_commands.shutdown
    elif command == Command.REBOOT.value:
        command_args = platform_commands.reboot
    else:
        raise ValueError(f"Unsupported command: {command}")

    if dry_run:
        return f"Dry run: {' '.join(command_args)}"

    process = await asyncio.create_subprocess_exec(
        *command_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        stderr_text = stderr.decode().strip()
        raise RuntimeError(stderr_text or f"Command failed with exit code {process.returncode}")

    stdout_text = stdout.decode().strip()
    return stdout_text or f"Command executed: {' '.join(command_args)}"
