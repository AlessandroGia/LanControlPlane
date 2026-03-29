from enum import StrEnum


class HostState(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    WAKING = "waking"
    SHUTTING_DOWN = "shutting_down"
    UNKNOWN = "unknown"
