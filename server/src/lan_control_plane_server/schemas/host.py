import re
from datetime import datetime

from lan_control_plane_shared.enums.host_state import HostState
from pydantic import BaseModel, Field, IPvAnyAddress, field_validator

MAC_ADDRESS_REGEX = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")


class HostRead(BaseModel):
    id: str
    name: str
    hostname: str
    ip_address: str | None
    mac_address: str | None
    state: HostState
    is_managed: bool
    created_at: datetime
    updated_at: datetime


class HostNetworkUpdate(BaseModel):
    ip_address: IPvAnyAddress | None = Field(default=None)
    mac_address: str | None = Field(default=None)

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, value: str | None) -> str | None:
        if value is None:
            return None

        if not MAC_ADDRESS_REGEX.fullmatch(value):
            raise ValueError("Invalid MAC address format")

        return value.upper().replace("-", ":")
