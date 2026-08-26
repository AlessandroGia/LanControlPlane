from typing import Literal

from pydantic import Field

from lan_control_plane_shared.enums.command import Command
from lan_control_plane_shared.protocol.base import MessageBase


class ClientGetHosts(MessageBase):
    type: Literal["get_hosts"] = "get_hosts"


class ClientCommandRequest(MessageBase):
    type: Literal["command_request"] = "command_request"
    request_id: str = Field(min_length=8, max_length=64)
    host_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    command: Command
