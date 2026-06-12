"""
ping_test.py
------------
Runs the Linux `ping` command via subprocess and parses:
  - packets sent
  - packets received
  - packet loss %
  - RTT min / avg / max / mdev

Returns a structured dict ready to be stored in SQLite.
"""

import subprocess
import re
from datetime import datetime


# ─────────────────────────────────────────────
# Core runner
# ─────────────────────────────────────────────

def run_ping(host: str, count: int = 10) -> dict:
    """
    Run `ping -c <count> <host>` and return parsed metrics.

    Args:
        host  : IP address or hostname to ping (e.g. "8.8.8.8")
        count : number of ICMP packets to send (default: 10)

    Returns:
        dict with keys:
            test_type, host, timestamp,
            packets_sent, packets_received, packet_loss_pct,
            rtt_min_ms, rtt_avg_ms, rtt_max_ms, rtt_mdev_ms,
            raw_output, error
    """
    result = _build_empty_result(host)

    # Build command
    cmd = ["ping", "-c", str(count), host]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=count + 10          # generous timeout
        )

        result["raw_output"] = proc.stdout + proc.stderr

        if proc.returncode != 0 and not proc.stdout:
            result["error"] = f"ping command failed (return code {proc.returncode})"
            return result

        # Parse output
        _parse_ping_output(proc.stdout, result)

    except subprocess.TimeoutExpired:
        result["error"] = f"ping timed out after {count + 10} seconds"

    except FileNotFoundError:
        result["error"] = "ping command not found. Install: sudo apt install iputils-ping"

    except Exception as e:
        result["error"] = str(e)

    return result


# ─────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────

def _parse_ping_output(output: str, result: dict) -> None:
    """
    Parse raw ping stdout and fill in the result dict in-place.

    Linux ping summary lines look like:
      5 packets transmitted, 5 received, 0% packet loss, time 4004ms
      rtt min/avg/max/mdev = 12.345/15.678/22.901/3.456 ms
    """

    # ── Packet statistics line ──────────────────
    # Pattern: "N packets transmitted, N received, N% packet loss"
    pkt_pattern = re.compile(
        r"(\d+)\s+packets\s+transmitted,\s+"
        r"(\d+)\s+received,\s+"
        r"([\d.]+)%\s+packet\s+loss"
    )
    pkt_match = pkt_pattern.search(output)
    if pkt_match:
        result["packets_sent"]      = int(pkt_match.group(1))
        result["packets_received"]  = int(pkt_match.group(2))
        result["packet_loss_pct"]   = float(pkt_match.group(3))

    # ── RTT summary line ────────────────────────
    # Pattern: "rtt min/avg/max/mdev = 12.3/15.6/22.9/3.4 ms"
    rtt_pattern = re.compile(
        r"rtt\s+min/avg/max/mdev\s*=\s*"
        r"([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)\s+ms"
    )
    rtt_match = rtt_pattern.search(output)
    if rtt_match:
        result["rtt_min_ms"]  = float(rtt_match.group(1))
        result["rtt_avg_ms"]  = float(rtt_match.group(2))
        result["rtt_max_ms"]  = float(rtt_match.group(3))
        result["rtt_mdev_ms"] = float(rtt_match.group(4))


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _build_empty_result(host: str) -> dict:
    """Return a blank result dict with all expected keys."""
    return {
        "test_type":         "ping",
        "host":              host,
        "timestamp":         datetime.now().isoformat(timespec="seconds"),
        "packets_sent":      None,
        "packets_received":  None,
        "packet_loss_pct":   None,
        "rtt_min_ms":        None,
        "rtt_avg_ms":        None,
        "rtt_max_ms":        None,
        "rtt_mdev_ms":       None,
        "raw_output":        "",
        "error":             None,
    }


def format_result(result: dict) -> str:
    """
    Return a human-readable CLI string from a ping result dict.
    Used by main.py to print output to terminal.
    """
    lines = []
    lines.append("=" * 48)
    lines.append(f"  Ping Test — {result['host']}")
    lines.append(f"  Time      : {result['timestamp']}")
    lines.append("=" * 48)

    if result["error"]:
        lines.append(f"  ERROR     : {result['error']}")
        lines.append("=" * 48)
        return "\n".join(lines)

    sent = result["packets_sent"]
    recv = result["packets_received"]
    loss = result["packet_loss_pct"]

    lines.append(f"  Sent      : {sent}")
    lines.append(f"  Received  : {recv}")
    lines.append(f"  Loss      : {loss}%")

    if result["rtt_avg_ms"] is not None:
        lines.append(f"  RTT min   : {result['rtt_min_ms']} ms")
        lines.append(f"  RTT avg   : {result['rtt_avg_ms']} ms")
        lines.append(f"  RTT max   : {result['rtt_max_ms']} ms")
        lines.append(f"  RTT mdev  : {result['rtt_mdev_ms']} ms")
    else:
        lines.append("  RTT       : (not available — all packets lost)")

    lines.append("=" * 48)
    return "\n".join(lines)
