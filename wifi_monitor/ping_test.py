# wifi_monitor/ping_test.py

import subprocess
import re
from wifi_monitor.utils import is_tool_installed, format_timestamp


def run_ping_test(host: str, count: int = 10) -> dict:
    """
    Run ping and return a structured result dict.
    Always returns a dict with 'status' key — either SUCCESS or FAILED.
    """
    if not is_tool_installed("ping"):
        return _error_result(host, count, error="ping not found on this system")

    cmd = ["ping", "-c", str(count), host]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=count + 10
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


def _parse_ping_output(raw_output: str, host: str, count: int) -> dict:
    """
    Parse Linux ping output into a structured dict.

    Linux ping output looks like:
    --- 8.8.8.8 ping statistics ---
    10 packets transmitted, 10 received, 0% packet loss, time 9010ms
    rtt min/avg/max/mdev = 10.123/14.234/22.701/3.456 ms
    """

    # --- Parse packet stats ---
    # Matches: "10 packets transmitted, 10 received, 0% packet loss"
    packet_pattern = re.search(
        r"(\d+) packets transmitted,\s*(\d+) received,\s*([\d.]+)% packet loss",
        raw_output
    )

    # --- Parse RTT stats ---
    # Matches: "rtt min/avg/max/mdev = 10.123/14.234/22.701/3.456 ms"
    rtt_pattern = re.search(
        r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms",
        raw_output
    )

    # If packet stats not found, the host was unreachable
    if not packet_pattern:
        return _error_result(
            host=host,
            count=count,
            error=f"Could not parse ping output. Host may be unreachable.\n{raw_output[:300]}",
            raw_output=raw_output
        )

    packets_sent     = int(packet_pattern.group(1))
    packets_received = int(packet_pattern.group(2))
    packet_loss_pct  = float(packet_pattern.group(3))

    # RTT stats are absent when 100% packet loss
    rtt_min = rtt_max = rtt_avg = rtt_mdev = None
    if rtt_pattern:
        rtt_min  = float(rtt_pattern.group(1))
        rtt_avg  = float(rtt_pattern.group(2))
        rtt_max  = float(rtt_pattern.group(3))
        rtt_mdev = float(rtt_pattern.group(4))

    return {
        "test_type":         "ping",
        "status":            "SUCCESS",        # ← THIS KEY is what main.py checks
        "host":              host,
        "server":            None,
        "interface":         None,
        "ssid":              None,
        "ip_address":        None,
        "local_ip":          None,
        "remote_ip":         host,
        "protocol":          "ICMP",
        "duration_seconds":  None,
        "bandwidth_target":  None,
        "packets_sent":      packets_sent,
        "packets_received":  packets_received,
        "packet_loss_pct":   packet_loss_pct,
        "rtt_min_ms":        rtt_min,
        "rtt_avg_ms":        rtt_avg,
        "rtt_max_ms":        rtt_max,
        "rtt_mdev_ms":       rtt_mdev,
        "throughput_mbps":   None,
        "jitter_ms":         None,
        "iperf_version":     None,
        "raw_output":        raw_output,
        "error":             None,
        "notes":             None,
        "timestamp":         format_timestamp()
    }


def _error_result(host: str, count: int,
                  error: str, raw_output: str = "") -> dict:
    """
    Always return a complete dict — even on failure.
    Every key that storage.py and main.py expect must be present.
    """
    return {
        "test_type":         "ping",
        "status":            "FAILED",         # ← always set, never missing
        "host":              host,
        "server":            None,
        "interface":         None,
        "ssid":              None,
        "ip_address":        None,
        "local_ip":          None,
        "remote_ip":         None,
        "protocol":          "ICMP",
        "duration_seconds":  None,
        "bandwidth_target":  None,
        "packets_sent":      count,
        "packets_received":  0,
        "packet_loss_pct":   100.0,
        "rtt_min_ms":        None,
        "rtt_avg_ms":        None,
        "rtt_max_ms":        None,
        "rtt_mdev_ms":       None,
        "throughput_mbps":   None,
        "jitter_ms":         None,
        "iperf_version":     None,
        "raw_output":        raw_output,
        "error":             error,
        "notes":             None,
        "timestamp":         format_timestamp()
    }