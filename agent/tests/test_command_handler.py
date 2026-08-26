import pytest

from lan_control_plane_agent.handlers.command_handler import handle_command


@pytest.mark.asyncio
async def test_dry_run_does_not_execute_platform_command() -> None:
    result = await handle_command(command="shutdown", dry_run=True)
    assert result.startswith("Dry run:")


@pytest.mark.asyncio
async def test_unknown_command_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported command"):
        await handle_command(command="format-disk", dry_run=True)
