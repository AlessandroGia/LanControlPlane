from __future__ import annotations

import time

import psutil

BOOT_TIME = psutil.boot_time()


def get_cpu_usage() -> float:
    return float(psutil.cpu_percent(interval=None))


def get_memory_usage() -> float:
    return float(psutil.virtual_memory().percent)


def get_uptime_seconds() -> int:
    return int(time.time() - BOOT_TIME)
