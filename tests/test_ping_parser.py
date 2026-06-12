"""
tests/test_ping_parser.py
--------------------------
Unit tests for ping_test._parse_ping_output()

These tests do NOT run the real ping command.
They test the PARSER with real-looking sample outputs.

Run with:
    python -m pytest tests/ -v
    # or without pytest:
    python tests/test_ping_parser.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wifi_monitor.ping_test import _parse_ping_output, _build_empty_result


# ─────────────────────────────────────────────
# Sample outputs (real Linux ping output)
# ─────────────────────────────────────────────

SAMPLE_SUCCESS = """
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=116 time=12.4 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=116 time=13.1 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=116 time=11.8 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=116 time=14.2 ms
64 bytes from 8.8.8.8: icmp_seq=5 ttl=116 time=12.9 ms

--- 8.8.8.8 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4004ms
rtt min/avg/max/mdev = 11.800/12.880/14.200/0.821 ms
"""

SAMPLE_PARTIAL_LOSS = """
PING 192.168.1.99 (192.168.1.99) 56(84) bytes of data.
64 bytes from 192.168.1.99: icmp_seq=1 ttl=64 time=1.23 ms
64 bytes from 192.168.1.99: icmp_seq=3 ttl=64 time=1.45 ms

--- 192.168.1.99 ping statistics ---
5 packets transmitted, 2 received, 60% packet loss, time 4100ms
rtt min/avg/max/mdev = 1.230/1.340/1.450/0.110 ms
"""

SAMPLE_FULL_LOSS = """
PING 192.0.2.1 (192.0.2.1) 56(84) bytes of data.

--- 192.0.2.1 ping statistics ---
5 packets transmitted, 0 received, 100% packet loss, time 4000ms
"""


# ─────────────────────────────────────────────
# Test functions
# ─────────────────────────────────────────────

def test_successful_ping():
    result = _build_empty_result("8.8.8.8")
    _parse_ping_output(SAMPLE_SUCCESS, result)

    assert result["packets_sent"]     == 5,    f"Expected 5, got {result['packets_sent']}"
    assert result["packets_received"] == 5,    f"Expected 5, got {result['packets_received']}"
    assert result["packet_loss_pct"]  == 0.0,  f"Expected 0.0, got {result['packet_loss_pct']}"
    assert result["rtt_min_ms"]       == 11.8, f"Expected 11.8, got {result['rtt_min_ms']}"
    assert result["rtt_avg_ms"]       == 12.88,f"Expected 12.88, got {result['rtt_avg_ms']}"
    assert result["rtt_max_ms"]       == 14.2, f"Expected 14.2, got {result['rtt_max_ms']}"
    print("  [PASS] test_successful_ping")


def test_partial_loss():
    result = _build_empty_result("192.168.1.99")
    _parse_ping_output(SAMPLE_PARTIAL_LOSS, result)

    assert result["packets_sent"]     == 5
    assert result["packets_received"] == 2
    assert result["packet_loss_pct"]  == 60.0
    assert result["rtt_avg_ms"]       == 1.34
    print("  [PASS] test_partial_loss")


def test_full_loss():
    result = _build_empty_result("192.0.2.1")
    _parse_ping_output(SAMPLE_FULL_LOSS, result)

    assert result["packets_sent"]     == 5
    assert result["packets_received"] == 0
    assert result["packet_loss_pct"]  == 100.0
    assert result["rtt_min_ms"]       is None   # no RTT line when all packets lost
    assert result["rtt_avg_ms"]       is None
    print("  [PASS] test_full_loss")


def test_empty_output():
    result = _build_empty_result("bad-host")
    _parse_ping_output("", result)

    assert result["packets_sent"]    is None
    assert result["rtt_avg_ms"]      is None
    print("  [PASS] test_empty_output")


# ─────────────────────────────────────────────
# Runner (without pytest)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\nRunning ping parser unit tests...\n")
    test_successful_ping()
    test_partial_loss()
    test_full_loss()
    test_empty_output()
    print("\nAll tests passed! ✅\n")
