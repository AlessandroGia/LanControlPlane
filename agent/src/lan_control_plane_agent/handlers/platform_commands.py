from __future__ import annotations

import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformCommands:
    shutdown: list[str]
    reboot: list[str]


def get_platform_commands() -> PlatformCommands:
    system = platform.system().lower()

    if system == "linux":
        return PlatformCommands(
            shutdown=["shutdown", "-h", "now"],
            reboot=["reboot"],
        )

    if system == "darwin":
        return PlatformCommands(
            shutdown=["shutdown", "-h", "now"],
            reboot=["shutdown", "-r", "now"],
        )

    if system == "windows":
        return PlatformCommands(
            shutdown=["shutdown", "/s", "/t", "0"],
            reboot=["shutdown", "/r", "/t", "0"],
        )

    raise RuntimeError(f"Unsupported operating system: {platform.system()}")
