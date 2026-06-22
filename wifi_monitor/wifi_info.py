"""
wifi_info.py
------------
Collect Wi-Fi connection metadata.
Uses nmcli device status for interface/SSID,
and the `ip` command for IP/gateway (more reliable across distros).
"""
from __future__ import annotations
import re
import subprocess
from wifi_monitor.logger import logger


def get_wifi_info() -> dict:
    info: dict = {"available": False}
    try:
        iface = _get_wifi_interface()
        ssid  = _get_ssid()
        ip    = _get_ip_address(iface) if iface else None
        gw    = _get_gateway()
        sig   = _get_active_signal() if iface else None

        info.update({
            "available":  bool(iface or ssid or ip),
            "ssid":       ssid  or "N/A",
            "interface":  iface or "N/A",
            "ip_address": ip    or "N/A",
            "gateway":    gw    or "N/A",
            "signal_strength": sig,
        })
        logger.debug("wifi-info: %s", info)
        return info

    except Exception as exc:
        info["error"] = str(exc)
        logger.warning("wifi-info failed: %s", exc)
        return info



def _run(cmd: list[str], timeout: int = 5) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.stdout


def _get_wifi_interface() -> str | None:
    """Return connected wifi interface via `nmcli device status`."""
    try:
        out = _run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device", "status"])
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 3 and parts[1] in ("wifi", "802-11-wireless") and "connected" in parts[2]:
                return parts[0]
    except Exception:
        pass

    # Fallback: scan ip link for wlan/wlp interfaces
    try:
        out = _run(["ip", "-o", "link", "show"])
        m = re.search(r"\d+: (wl\w+):", out)
        return m.group(1) if m else None
    except Exception:
        return None


def _get_ssid() -> str | None:
    """Return active SSID via nmcli dev wifi."""
    try:
        proc = subprocess.run(
            ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
            capture_output=True, timeout=5,
        )
        # decode manually to avoid encoding issues
        out = proc.stdout.decode("utf-8", errors="replace")
        for line in out.splitlines():
            line = line.strip()
            if line.lower().startswith("yes:"):
                ssid = line.split(":", 1)[1].strip()
                if ssid:
                    return ssid
    except Exception:
        pass

    # Fallback: active connection name via nmcli connection show --active
    try:
        proc = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"],
            capture_output=True, timeout=5,
        )
        out = proc.stdout.decode("utf-8", errors="replace")
        for line in out.splitlines():
            parts = line.strip().split(":")
            if len(parts) >= 2 and "wireless" in parts[-1].lower():
                return parts[0].strip()
    except Exception:
        pass

    return None


def _get_ip_address(iface: str) -> str | None:
    """Return IPv4 address for the interface via `ip addr`."""
    try:
        out = _run(["ip", "-4", "addr", "show", iface])
        m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", out)
        return m.group(1) if m else None
    except Exception:
        return None


def _get_gateway() -> str | None:
    """Return default gateway via `ip route`."""
    try:
        out = _run(["ip", "route", "show", "default"])
        m = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", out)
        return m.group(1) if m else None
    except Exception:
        return None


def _get_active_signal() -> int | None:
    try:
        proc = subprocess.run(
            ["nmcli", "-t", "-f", "active,signal", "dev", "wifi"],
            capture_output=True, timeout=5,
        )
        # decode manually to avoid encoding issues
        out = proc.stdout.decode("utf-8", errors="replace")
        for line in out.splitlines():
            line = line.strip()
            if line.lower().startswith("yes:"):
                sig_str = line.split(":", 1)[1].strip()
                if sig_str:
                    return int(sig_str)
    except Exception:
        pass
    return None