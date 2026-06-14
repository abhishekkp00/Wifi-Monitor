"""
packet_capture.py
-----------------
Optional tcpdump wrapper for debugging.
Requires sudo or cap_net_raw capability.
"""
from __future__ import annotations
import os
import subprocess
from datetime import datetime
from wifi_monitor.config import get_cfg
from wifi_monitor.logger import logger


def start_capture(
    interface: str = "any",
    output_dir: str | None = None,
    duration: int | None = None,
) -> dict:
    output_dir = output_dir or get_cfg("logging", "log_dir", "data/logs")
    duration   = duration   or get_cfg("throughput", "default_duration", 10)

    os.makedirs(output_dir, exist_ok=True)
    ts       = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    pcap_path = os.path.join(output_dir, f"capture_{ts}.pcap")

    cmd = ["tcpdump", "-i", interface, "-s", "65535",
           "-w", pcap_path, "-G", str(duration), "-W", "1"]

    logger.info("tcpdump cmd: %s", " ".join(cmd))
    try:
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        return {"status": "STARTED", "pid": proc.pid, "pcap_path": pcap_path, "process": proc}
    except FileNotFoundError:
        return {"status": "TOOL_NOT_FOUND",
                "error": "tcpdump not found. sudo apt install tcpdump"}
    except PermissionError:
        return {"status": "PERMISSION_DENIED",
                "error": "Run as root or grant cap_net_raw: sudo setcap cap_net_raw+ep $(which tcpdump)"}