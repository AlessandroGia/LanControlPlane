import asyncio
import logging
import platform

LOGGER = logging.getLogger(__name__)


async def execute_shutdown(*, dry_run: bool) -> str:
    if dry_run:
        LOGGER.info("DRY_RUN enabled: shutdown simulated")
        await asyncio.sleep(2)
        return "shutdown simulated successfully"

    system_name = platform.system().lower()

    if system_name == "linux":
        process = await asyncio.create_subprocess_exec(
            "shutdown",
            "-h",
            "now",
        )
        return_code = await process.wait()
        if return_code != 0:
            raise RuntimeError(f"shutdown failed with return code {return_code}")
        return "shutdown executed successfully"

    raise RuntimeError(f"shutdown not supported on platform: {system_name}")
