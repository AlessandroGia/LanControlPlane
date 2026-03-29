import logging

from lan_control_plane_agent.executors.reboot import execute_reboot
from lan_control_plane_agent.executors.shutdown import execute_shutdown

LOGGER = logging.getLogger(__name__)


async def handle_command(*, command: str, dry_run: bool) -> str:
    LOGGER.info("Handling command: %s", command)

    if command == "shutdown":
        return await execute_shutdown(dry_run=dry_run)

    if command == "reboot":
        return await execute_reboot(dry_run=dry_run)

    raise RuntimeError(f"Unsupported command: {command}")
