"""
utils.py
--------
Shared helper utilities used across modules.
"""

import shutil
import sys


def check_command_available(cmd: str) -> bool:
    """
    Return True if a shell command/binary is available on this system.

    Example:
        check_command_available("ping")   -> True / False
        check_command_available("iperf3") -> True / False
    """
    return shutil.which(cmd) is not None


def require_command(cmd: str, install_hint: str = "") -> None:
    """
    Exit with a helpful message if a required command is not installed.

    Args:
        cmd          : command name e.g. "iperf3"
        install_hint : e.g. "sudo apt install iperf3"
    """
    if not check_command_available(cmd):
        msg = f"[ERROR] Required command not found: '{cmd}'"
        if install_hint:
            msg += f"\n        Install with: {install_hint}"
        print(msg)
        sys.exit(1)


def print_separator(char: str = "─", width: int = 48) -> None:
    """Print a separator line for CLI output."""
    print(char * width)


def format_optional(value, suffix: str = "", na: str = "N/A") -> str:
    """
    Safely format a value that might be None.

    Example:
        format_optional(12.5, " ms")  -> "12.5 ms"
        format_optional(None)         -> "N/A"
    """
    if value is None:
        return na
    return f"{value}{suffix}"
