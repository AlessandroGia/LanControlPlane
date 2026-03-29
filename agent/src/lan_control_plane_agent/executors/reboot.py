import asyncio
import logging
import platform

LOGGER = logging.getLogger(__name__)


async def execute_reboot(*, dry_run: bool) -> str:
    if dry_run:
        LOGGER.info("DRY_RUN enabled: reboot simulated")
        await asyncio.sleep(2)
        return "reboot simulated successfully"

    system_name = platform.system().lower()

    if system_name == "linux":
        process = await asyncio.create_subprocess_exec(
            "reboot",
        )
        return_code = await process.wait()
        if return_code != 0:
            raise RuntimeError(f"reboot failed with return code {return_code}")
        return "reboot executed successfully"

    raise RuntimeError(f"reboot not supported on platform: {system_name}")
