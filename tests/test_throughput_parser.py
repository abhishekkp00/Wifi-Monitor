"""Unit tests for throughput_test._parse_iperf_json()."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wifi_monitor.throughput_test import _parse_iperf_json


SAMPLE_TCP_SUCCESS = {
    "start": {
        "connected": [
            {
                "socket": 4,
                "local_host": "127.0.0.1",
                "local_port": 50000,
                "remote_host": "127.0.0.1",
                "remote_port": 5201
            }
        ]
    },
    "intervals": [
        {
            "streams": [
                {
                    "socket": 4,
                    "start": 0.0,
                    "end": 1.0,
                    "seconds": 1.0,
                    "bytes": 125000000,
                    "bits_per_second": 1000000000.0,
                    "retransmits": 0,
                    "rtt": 0.05,
                    "rttvar": 0.02,
                    "pmtu": 65535,
                    "omitted": False
                }
            ],
            "sum": {
                "start": 0.0,
                "end": 1.0,
                "seconds": 1.0,
                "bytes": 125000000,
                "bits_per_second": 1000000000.0,
                "retransmits": 0,
                "omitted": False
            }
        }
    ],
    "end": {
        "streams": [
            {
                "sender": {
                    "socket": 4,
                    "start": 0.0,
                    "end": 10.0,
                    "seconds": 10.0,
                    "bytes": 1250000000,
                    "bits_per_second": 1000000000.0,
                    "retransmits": 0,
                    "max_rtt": 0.08,
                    "min_rtt": 0.03,
                    "mean_rtt": 0.05
                },
                "receiver": {
                    "socket": 4,
                    "start": 0.0,
                    "end": 10.0,
                    "seconds": 10.0,
                    "bytes": 1250000000,
                    "bits_per_second": 1000000000.0
                }
            }
        ],
        "sum_sent": {
            "start": 0.0,
            "end": 10.0,
            "seconds": 10.0,
            "bytes": 1250000000,
            "bits_per_second": 1000000000.0,
            "retransmits": 0
        },
        "sum_received": {
            "start": 0.0,
            "end": 10.0,
            "seconds": 10.0,
            "bytes": 1250000000,
            "bits_per_second": 1000000000.0
        }
    }
}

# Successful UDP test output with jitter and packet loss
SAMPLE_UDP_SUCCESS = {
    "start": {},
    "intervals": [],
    "end": {
        "streams": [
            {
                "udp": {
                    "socket": 4,
                    "start": 0.0,
                    "end": 10.0,
                    "seconds": 10.0,
                    "bytes": 1250000000,
                    "bits_per_second": 1000000000.0,
                    "jitter_ms": 0.5,
                    "lost_packets": 50,
                    "packets": 10000,
                    "lost_percent": 0.5
                }
            }
        ],
        "sum": {
            "start": 0.0,
            "end": 10.0,
            "seconds": 10.0,
            "bytes": 1250000000,
            "bits_per_second": 1000000000.0,
            "jitter_ms": 0.5,
            "lost_packets": 50,
            "packets": 10000,
            "lost_percent": 0.5
        },
        "sum_received": {
            "start": 0.0,
            "end": 10.0,
            "seconds": 10.0,
            "bytes": 1250000000,
            "bits_per_second": 1000000000.0,
            "jitter_ms": 0.5
        }
    }
}


def test_tcp_success():
    """Test parsing successful TCP iperf3 output."""
    result = _parse_iperf_json(
        data=SAMPLE_TCP_SUCCESS,
        server="127.0.0.1",
        protocol="TCP",
        duration=10,
        bandwidth=None,
        raw_output="(sample TCP output)"
    )

    assert result["status"] == "SUCCESS", f"Expected SUCCESS, got {result['status']}"
    assert result["protocol"] == "TCP", f"Expected TCP, got {result['protocol']}"
    assert result["throughput_mbps"] == 1000.0, f"Expected 1000.0 Mbps, got {result['throughput_mbps']}"
    assert result["server"] == "127.0.0.1"
    assert result["test_type"] == "throughput"
    print("  [PASS] test_tcp_success")


def test_udp_success():
    """Test parsing successful UDP iperf3 output."""
    result = _parse_iperf_json(
        data=SAMPLE_UDP_SUCCESS,
        server="127.0.0.1",
        protocol="UDP",
        duration=10,
        bandwidth="100M",
        raw_output="(sample UDP output)"
    )

    assert result["status"] == "SUCCESS", f"Expected SUCCESS, got {result['status']}"
    assert result["protocol"] == "UDP", f"Expected UDP, got {result['protocol']}"
    assert result["throughput_mbps"] == 1000.0, f"Expected 1000.0 Mbps, got {result['throughput_mbps']}"
    assert result["jitter_ms"] == 0.5, f"Expected jitter 0.5 ms, got {result['jitter_ms']}"
    assert result["packet_loss_pct"] == 0.5, f"Expected 0.5% loss, got {result['packet_loss_pct']}"
    assert result["test_type"] == "throughput"
    print("  [PASS] test_udp_success")


if __name__ == "__main__":
    print("\nRunning throughput parser tests...\n")
    test_tcp_success()
    test_udp_success()
    print("\nAll tests passed!\n")
