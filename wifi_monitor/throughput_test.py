"""Throughput test module using iperf3."""

import subprocess
import json
import datetime
from wifi_monitor.utils import is_tool_installed, format_timestamp


def run_tcp_test(server: str, duration: int = 10, reverse: bool = False) -> dict:
    """Run a TCP throughput test using iperf3."""
    cmd = [
        "iperf3",
        "-c", server,
        "-t", str(duration),
        "-J"
    ]

    if reverse:
        cmd.append("-R")

    return _run_iperf(cmd, server=server, protocol="TCP", duration=duration)


def run_udp_test(server: str, duration: int = 10,
                 bandwidth: str = "100M", reverse: bool = False) -> dict:
    """Run a UDP throughput test using iperf3."""
    cmd = [
        "iperf3",
        "-c", server,
        "-t", str(duration),
        "-u",
        "-b", bandwidth,
        "-J"              # JSON output
    ]

    if reverse:
        cmd.append("-R")

    return _run_iperf(cmd, server=server, protocol="UDP",
                      duration=duration, bandwidth=bandwidth)


def _run_iperf(cmd: list, server: str, protocol: str,
               duration: int, bandwidth: str = None) -> dict:
    """Internal helper: runs the iperf3 command and parses JSON output."""
    if not is_tool_installed("iperf3"):
        return _error_result(
            server=server,
            protocol=protocol,
            duration=duration,
            error="iperf3 not found. Install it with: sudo apt install iperf3"
        )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=duration + 15
        )
    except subprocess.TimeoutExpired:
        return _error_result(
            server=server,
            protocol=protocol,
            duration=duration,
            error=f"iperf3 timed out after {duration + 15}s. Server may be unreachable."
        )
    except FileNotFoundError:
        return _error_result(
            server=server,
            protocol=protocol,
            duration=duration,
            error="iperf3 binary not found. Install it with: sudo apt install iperf3"
        )
    except Exception as e:
        return _error_result(
            server=server,
            protocol=protocol,
            duration=duration,
            error=f"Unexpected error running iperf3: {str(e)}"
        )

    raw_output = result.stdout or result.stderr or "(empty output)"

    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip()
        return _error_result(
            server=server,
            protocol=protocol,
            duration=duration,
            error=f"iperf3 failed (exit {result.returncode}): {error_msg}",
            raw_output=raw_output
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return _error_result(
            server=server,
            protocol=protocol,
            duration=duration,
            error="Failed to parse iperf3 JSON output. Got: " + result.stdout[:200],
            raw_output=raw_output
        )

    return _parse_iperf_json(
        data=data,
        server=server,
        protocol=protocol,
        duration=duration,
        bandwidth=bandwidth,
        raw_output=raw_output
    )


def _parse_iperf_json(data: dict, server: str, protocol: str,
                      duration: int, bandwidth: str, raw_output: str) -> dict:
    """Extract metrics from the iperf3 JSON structure."""
    try:
        end = data.get("end", {})

        sum_received = end.get("sum_received", {})
        sum_sent = end.get("sum_sent", {})

        throughput_bps = sum_received.get("bits_per_second") \
                         or sum_sent.get("bits_per_second", 0)
        throughput_mbps = round(throughput_bps / 1_000_000, 2)

        jitter_ms = None
        loss_pct = None

        if protocol == "UDP":
            streams = end.get("streams", [])
            if streams:
                udp_stats = streams[0].get("udp", {})
                jitter_ms = round(udp_stats.get("jitter_ms", 0), 3)
                loss_pct = round(udp_stats.get("lost_percent", 0), 2)

        start_info = data.get("start", {})
        iperf_version = start_info.get("version", "unknown")
        connected = start_info.get("connected", [{}])
        local_ip = connected[0].get("local_host", "unknown") if connected else "unknown"
        remote_ip = connected[0].get("remote_host", server) if connected else server

        return {
            "test_type": "throughput",
            "server": server,
            "protocol": protocol,
            "duration_seconds": duration,
            "bandwidth_target": bandwidth,
            "throughput_mbps": throughput_mbps,
            "jitter_ms": jitter_ms,
            "packet_loss_pct": loss_pct,
            "local_ip": local_ip,
            "remote_ip": remote_ip,
            "iperf_version": iperf_version,
            "timestamp": format_timestamp(),
            "status": "SUCCESS",
            "raw_output": raw_output,
            "error": None
        }

    except (KeyError, IndexError, TypeError) as e:
        return _error_result(
            server=server,
            protocol=protocol,
            duration=duration,
            error=f"JSON parsed but metric extraction failed: {str(e)}",
            raw_output=raw_output
        )


def _error_result(server: str, protocol: str, duration: int,
                  error: str, raw_output: str = "") -> dict:
    """Return a consistent error dict with all required keys."""
    return {
        "test_type": "throughput",
        "server": server,
        "protocol": protocol,
        "duration_seconds": duration,
        "bandwidth_target": None,
        "throughput_mbps": None,
        "jitter_ms": None,
        "packet_loss_pct": None,
        "local_ip": None,
        "remote_ip": None,
        "iperf_version": None,
        "timestamp": format_timestamp(),
        "status": "FAILED",
        "raw_output": raw_output,
        "error": error
    }
