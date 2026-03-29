from enum import StrEnum


class Command(StrEnum):
    WAKE = "wake"
    SHUTDOWN = "shutdown"
    REBOOT = "reboot"
