# wifi_monitor/ping_test.py

import re
import subprocess

from wifi_monitor.utils import is_tool_installed, format_timestamp


def run_ping_test(host: str, count: int = 10, interval: float | None = None) -> dict:
    """
    Run ping and return a structured result dict.
    Always returns a dict with 'status' key — either SUCCESS or FAILED.
    """
    if not is_tool_installed("ping"):
        return _error_result(host, count, error="ping not found on this system")

    cmd = ["ping", "-c", str(count)]
    if interval is not None:
        cmd += ["-i", str(interval)]
    cmd.append(host)

    timeout = int(count * (interval or 1.0)) + 10

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        raw_output = result.stdout + result.stderr

    except subprocess.TimeoutExpired:
        return _error_result(host, count, error=f"ping timed out after {count + 10}s")
    except FileNotFoundError:
        return _error_result(host, count, error="ping binary not found")
    except Exception as e:
        return _error_result(host, count, error=str(e))

    return _parse_ping_output(
        raw_output=raw_output,
        host=host,
        count=count
    )


def ping(*args, **kwargs):
    return run_ping_test(*args, **kwargs)

def run_ping(*args, **kwargs):
    return run_ping_test(*args, **kwargs)


def _parse_ping_output(raw_output: str, host: str, count: int) -> dict:
    packet_pattern = re.search(
        r"(\d+) packets transmitted,\s*(\d+) received,\s*([\d.]+)% packet loss",
        raw_output
    )

    rtt_pattern = re.search(
        r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms",
        raw_output
    )

    if not packet_pattern:
        return _error_result(
            host=host,
            count=count,
            error=f"Could not parse ping output. Host may be unreachable.\n{raw_output[:300]}",
            raw_output=raw_output
        )

    packets_sent = int(packet_pattern.group(1))
    packets_received = int(packet_pattern.group(2))
    packet_loss_pct = float(packet_pattern.group(3))

    rtt_min = rtt_max = rtt_avg = rtt_mdev = None
    if rtt_pattern:
        rtt_min = float(rtt_pattern.group(1))
        rtt_avg = float(rtt_pattern.group(2))
        rtt_max = float(rtt_pattern.group(3))
        rtt_mdev = float(rtt_pattern.group(4))

    return {
        "test_type": "ping",
        "status": "SUCCESS",
        "host": host,
        "server": None,
        "interface": None,
        "ssid": None,
        "ip_address": None,
        "local_ip": None,
        "remote_ip": host,
        "protocol": "ICMP",
        "duration_seconds": None,
        "bandwidth_target": None,
        "packets_sent": packets_sent,
        "packets_received": packets_received,
        "packet_loss_pct": packet_loss_pct,
        "rtt_min_ms": rtt_min,
        "rtt_avg_ms": rtt_avg,
        "rtt_max_ms": rtt_max,
        "rtt_mdev_ms": rtt_mdev,
        "throughput_mbps": None,
        "jitter_ms": None,
        "iperf_version": None,
        "raw_output": raw_output,
        "error": None,
        "error_message": None,
        "notes": None,
        "timestamp": format_timestamp()
    }


def _error_result(host: str, count: int, error: str, raw_output: str = "") -> dict:
    return {
        "test_type": "ping",
        "status": "FAILED",
        "host": host,
        "server": None,
        "interface": None,
        "ssid": None,
        "ip_address": None,
        "local_ip": None,
        "remote_ip": None,
        "protocol": "ICMP",
        "duration_seconds": None,
        "bandwidth_target": None,
        "packets_sent": count,
        "packets_received": 0,
        "packet_loss_pct": 100.0,
        "rtt_min_ms": None,
        "rtt_avg_ms": None,
        "rtt_max_ms": None,
        "rtt_mdev_ms": None,
        "throughput_mbps": None,
        "jitter_ms": None,
        "iperf_version": None,
        "raw_output": raw_output,
        "error": error,
        "error_message": error,
        "notes": None,
        "timestamp": format_timestamp()
    }