from lan_control_plane_shared.enums.command import Command
from lan_control_plane_shared.protocol.base import MessageBase


class ClientAuth(MessageBase):
    type: str = "auth"
    token: str


class ClientGetHosts(MessageBase):
    type: str = "get_hosts"


class ClientCommandRequest(MessageBase):
    type: str = "command_request"
    request_id: str
    host_id: str
    command: Command
