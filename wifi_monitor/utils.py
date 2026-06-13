"""
utils.py
--------
Shared helper utilities used across modules.
"""

"""
Shared utility functions used across all modules.
Keep this file simple — no business logic here.
"""

import shutil
import datetime


def is_tool_installed(tool_name: str) -> bool:
    """
    Check if a CLI tool is available on PATH.
    Uses shutil.which() — same as `which ping` in bash.

    Example:
        is_tool_installed("iperf3")  -> True or False
        is_tool_installed("tcpdump") -> True or False
    """
    return shutil.which(tool_name) is not None


def format_timestamp() -> str:
    """
    Return current UTC time as ISO 8601 string.
    Example: "2026-06-13T08:30:00.123456"
    Stored in DB so every result can be sorted chronologically.
    """
    return datetime.datetime.utcnow().isoformat()


def bits_to_mbps(bits_per_second: float) -> float:
    """
    Convert bits/sec to Megabits/sec.
    iperf3 JSON always returns bits_per_second.
    Divide by 1,000,000 (not 1,048,576) because network
    bandwidth uses SI units, not binary units.
    """
    if bits_per_second is None:
        return None
    return round(bits_per_second / 1_000_000, 2)


def safe_float(value, default=None):
    """
    Safely convert a value to float.
    Returns default if conversion fails.
    Prevents crashes when iperf3 returns unexpected types.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=None):
    """
    Safely convert a value to int.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default