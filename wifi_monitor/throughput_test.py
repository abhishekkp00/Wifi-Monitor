"""
throughput_test.py
------------------
Two backends:
  run_speedtest()   — uses speedtest-cli (internet speed, no server needed)
  run_throughput()  — uses iperf3 (LAN throughput, requires iperf3 server)

run_speedtest() is the default when the dashboard "Speed Test" button is clicked.
"""
from __future__ import annotations

import json
import os
import sys
import subprocess
from datetime import datetime, timezone

# Resolve speedtest-cli from the same Python environment (venv-safe)
_BIN_DIR = os.path.dirname(sys.executable)
_SPEEDTEST_BIN = os.path.join(_BIN_DIR, "speedtest-cli")

from wifi_monitor.config import get_cfg
from wifi_monitor.logger import logger
from wifi_monitor.utils import format_timestamp


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _bps_to_mbps(bps) -> float | None:
    if bps is None:
        return None
    return round(float(bps) / 1_000_000, 3)


def _safe_round(v) -> float | None:
    return None if v is None else round(float(v), 3)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── speedtest-cli backend ────────────────────────────────────────────────────

def run_speedtest() -> dict:
    """
    Run an internet speed test using speedtest-cli (no iperf3 server needed).
    Returns a result dict compatible with storage.save_result().
    """
    logger.info("Running speedtest-cli: %s", _SPEEDTEST_BIN)
    base = {
        "test_type": "throughput",
        "protocol": "TCP",
        "host": None,
        "server": None,
        "interface": None,
        "ssid": None,
        "ip_address": None,
        "local_ip": None,
        "remote_ip": None,
        "duration_seconds": None,
        "bandwidth_target": None,
        "bandwidth": None,
        "packets_sent": None,
        "packets_received": None,
        "packet_loss_pct": None,
        "rtt_min_ms": None,
        "rtt_avg_ms": None,
        "rtt_max_ms": None,
        "rtt_mdev_ms": None,
        "jitter_ms": None,
        "upload_mbps": None,
        "iperf_version": None,
        "notes": None,
        "raw_output": None,
        "error": None,
        "error_message": None,
        "timestamp": _now(),
    }

    try:
        proc = subprocess.run(
            [_SPEEDTEST_BIN, "--json"],
            capture_output=True, text=True, timeout=90
        )
        raw = proc.stdout.strip()
        base["raw_output"] = raw

        if proc.returncode != 0:
            msg = proc.stderr.strip() or "speedtest-cli failed"
            base.update({"status": "TOOL_ERROR", "error": msg, "error_message": msg})
            return base

        data = json.loads(raw)
        server_info = data.get("server", {})
        server_host = server_info.get("sponsor", "") + " (" + server_info.get("name", "") + ")"
        ping_ms     = _safe_round(data.get("ping"))

        base.update({
            "status":          "SUCCESS",
            "server":          server_host.strip() or "speedtest.net",
            "remote_ip":       server_info.get("host"),
            "throughput_mbps": _bps_to_mbps(data.get("download")),
            "upload_mbps":     _bps_to_mbps(data.get("upload")),
            "rtt_avg_ms":      ping_ms,
            "notes":           f"upload={_bps_to_mbps(data.get('upload'))} Mbps",
        })
        logger.info("speedtest done — dl=%.2f Mbps", base["throughput_mbps"] or 0)
        return base

    except FileNotFoundError:
        msg = f"speedtest-cli not found at {_SPEEDTEST_BIN}. Run: pip install speedtest-cli"
        base.update({"status": "TOOL_NOT_FOUND", "error": msg, "error_message": msg})
        return base
    except subprocess.TimeoutExpired:
        msg = "speedtest-cli timed out after 90 seconds"
        base.update({"status": "TIMEOUT", "error": msg, "error_message": msg})
        return base
    except json.JSONDecodeError:
        msg = "speedtest-cli did not return valid JSON"
        base.update({"status": "PARSE_ERROR", "error": msg, "error_message": msg})
        return base
    except Exception as exc:
        msg = str(exc)
        base.update({"status": "ERROR", "error": msg, "error_message": msg})
        return base


# ─── iperf3 backend ───────────────────────────────────────────────────────────

def run_throughput(
    server: str | None = None,
    duration: int | None = None,
    protocol: str | None = None,
    bandwidth: str | None = None,
    port: int | None = None,
) -> dict:
    """Run iperf3 test. Requires a running iperf3 server on target host."""
    server   = server   or get_cfg("throughput", "default_server",   "127.0.0.1")
    duration = duration or get_cfg("throughput", "default_duration",  10)
    protocol = (protocol or get_cfg("throughput", "default_protocol", "tcp")).lower()
    port     = port     or get_cfg("throughput", "default_port",      5201)

    cmd = ["iperf3", "-c", server, "-t", str(duration), "-p", str(port), "-J"]
    if protocol == "udp":
        cmd.append("-u")
        if bandwidth:
            cmd += ["-b", bandwidth]

    logger.info("Running iperf3: %s", " ".join(cmd))

    base = {
        "test_type": "throughput", "server": server, "protocol": protocol.upper(),
        "duration_seconds": duration, "bandwidth": bandwidth, "bandwidth_target": bandwidth,
        "host": None, "interface": None, "ssid": None, "ip_address": None,
        "local_ip": None, "remote_ip": None, "packets_sent": None, "packets_received": None,
        "packet_loss_pct": None, "rtt_min_ms": None, "rtt_avg_ms": None,
        "rtt_max_ms": None, "rtt_mdev_ms": None, "jitter_ms": None,
        "iperf_version": None, "raw_output": None, "notes": None,
        "error": None, "error_message": None, "timestamp": _now(),
    }

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 15)
        raw  = proc.stdout.strip()
        raw_err = proc.stderr.strip()
        base["raw_output"] = raw

        if proc.returncode != 0:
            msg = raw_err or raw or "iperf3 failed"
            base.update({"status": "TOOL_ERROR", "error": msg, "error_message": msg,
                          "throughput_mbps": None})
            return base

        data = json.loads(raw)
        return _parse_iperf_json(data, base)

    except FileNotFoundError:
        msg = "iperf3 not installed. Run: sudo apt install iperf3"
        base.update({"status": "TOOL_NOT_FOUND", "error": msg, "error_message": msg,
                     "throughput_mbps": None})
        return base
    except subprocess.TimeoutExpired:
        msg = f"iperf3 timed out after {duration + 15}s"
        base.update({"status": "TIMEOUT", "error": msg, "error_message": msg,
                     "throughput_mbps": None})
        return base
    except Exception as exc:
        msg = str(exc)
        base.update({"status": "ERROR", "error": msg, "error_message": msg,
                     "throughput_mbps": None})
        return base


def _parse_iperf_json(data: dict, base: dict = None, *,
                      server: str = "?", protocol: str = "TCP",
                      duration: int = 0, bandwidth=None,
                      raw_output: str = "") -> dict:
    """Parse iperf3 JSON. Accepts both call styles (old keyword API + new base dict)."""
    if base is None:
        base = {
            "test_type": "throughput", "server": server, "protocol": protocol,
            "duration_seconds": duration, "bandwidth": bandwidth,
            "bandwidth_target": bandwidth, "host": None, "interface": None,
            "ssid": None, "ip_address": None, "local_ip": None, "remote_ip": None,
            "packets_sent": None, "packets_received": None, "packet_loss_pct": None,
            "rtt_min_ms": None, "rtt_avg_ms": None, "rtt_max_ms": None,
            "rtt_mdev_ms": None, "jitter_ms": None, "upload_mbps": None,
            "iperf_version": None, "raw_output": raw_output, "notes": None,
            "error": None, "error_message": None, "timestamp": _now(),
        }
    base["status"] = "SUCCESS"
    try:
        end = data.get("end", {})
        proto = base["protocol"].upper()
        if proto == "UDP":
            s = end.get("sum", {})
            base["throughput_mbps"]  = _bps_to_mbps(s.get("bits_per_second"))
            base["jitter_ms"]        = _safe_round(s.get("jitter_ms"))
            base["packet_loss_pct"]  = _safe_round(s.get("lost_percent"))
        else:
            recv = end.get("sum_received", {})
            sent = end.get("sum_sent", {})
            bps  = recv.get("bits_per_second") or sent.get("bits_per_second")
            base["throughput_mbps"] = _bps_to_mbps(bps)

        if base.get("throughput_mbps") is None:
            msg = "Could not extract throughput from iperf3 JSON"
            base.update({"status": "PARSE_ERROR", "error": msg, "error_message": msg})
        return base
    except Exception as exc:
        msg = str(exc)
        base.update({"status": "PARSE_ERROR", "error": msg, "error_message": msg})
        return base