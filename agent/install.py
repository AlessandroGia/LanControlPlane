from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path


def main() -> int:
    agent_dir = Path(__file__).resolve().parent
    system = platform.system().lower()

    if system == "linux":
        script = agent_dir / "install_linux_service.sh"
        return subprocess.call(["bash", str(script)])

    if system == "darwin":
        script = agent_dir / "install_macos_service.sh"
        return subprocess.call(["bash", str(script)])

    if system == "windows":
        script = agent_dir / "install_windows_service.ps1"
        return subprocess.call(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ]
        )

    print(f"Unsupported operating system: {platform.system()}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
