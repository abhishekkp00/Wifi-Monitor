import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from wifi_monitor.ping_test import _parse_ping_output, _error_result

# ── Sample ping outputs (real Linux ping text) ──────────────

SAMPLE_SUCCESS = """PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=14.2 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=118 time=12.1 ms

--- 8.8.8.8 ping statistics ---
10 packets transmitted, 10 received, 0% packet loss, time 9010ms
rtt min/avg/max/mdev = 10.123/14.234/22.701/3.456 ms
"""

SAMPLE_PARTIAL_LOSS = """--- 1.1.1.1 ping statistics ---
10 packets transmitted, 8 received, 20% packet loss, time 9008ms
rtt min/avg/max/mdev = 11.000/15.000/25.000/4.000 ms
"""

SAMPLE_FULL_LOSS = """--- 10.0.0.99 ping statistics ---
5 packets transmitted, 0 received, 100% packet loss, time 4004ms
"""

SAMPLE_GARBAGE = "bash: ping: command not found"


class TestPingParserSuccess:

    def test_status_is_success(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["status"] == "SUCCESS"

    def test_packets_sent(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["packets_sent"] == 10

    def test_packets_received(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["packets_received"] == 10

    def test_packet_loss_zero(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["packet_loss_pct"] == 0.0

    def test_rtt_avg_correct(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["rtt_avg_ms"] == 14.234

    def test_rtt_min_correct(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["rtt_min_ms"] == 10.123

    def test_rtt_max_correct(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["rtt_max_ms"] == 22.701

    def test_rtt_mdev_correct(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["rtt_mdev_ms"] == 3.456

    def test_host_stored(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["host"] == "8.8.8.8"

    def test_test_type_is_ping(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["test_type"] == "ping"

    def test_timestamp_present(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["timestamp"] is not None

    def test_throughput_is_none_for_ping(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["throughput_mbps"] is None

    def test_jitter_is_none_for_ping(self):
        r = _parse_ping_output(SAMPLE_SUCCESS, "8.8.8.8", 10)
        assert r["jitter_ms"] is None


class TestPingParserPartialLoss:

    def test_packet_loss_20_percent(self):
        r = _parse_ping_output(SAMPLE_PARTIAL_LOSS, "1.1.1.1", 10)
        assert r["packet_loss_pct"] == 20.0

    def test_status_still_success_with_partial_loss(self):
        # Partial loss is a valid result — not a failure
        r = _parse_ping_output(SAMPLE_PARTIAL_LOSS, "1.1.1.1", 10)
        assert r["status"] == "SUCCESS"

    def test_packets_received_8(self):
        r = _parse_ping_output(SAMPLE_PARTIAL_LOSS, "1.1.1.1", 10)
        assert r["packets_received"] == 8


class TestPingParserFullLoss:

    def test_full_loss_status_success(self):
        # 100% loss is still a parseable result — status = SUCCESS
        # The loss_pct=100 is the data point, not a tool failure
        r = _parse_ping_output(SAMPLE_FULL_LOSS, "10.0.0.99", 5)
        assert r["status"] == "SUCCESS"

    def test_full_loss_rtt_is_none(self):
        # No RTT line when 100% loss
        r = _parse_ping_output(SAMPLE_FULL_LOSS, "10.0.0.99", 5)
        assert r["rtt_avg_ms"] is None
        assert r["rtt_min_ms"] is None
        assert r["rtt_max_ms"] is None

    def test_full_loss_pct_is_100(self):
        r = _parse_ping_output(SAMPLE_FULL_LOSS, "10.0.0.99", 5)
        assert r["packet_loss_pct"] == 100.0


class TestErrorResult:

    def test_error_result_has_failed_status(self):
        r = _error_result("8.8.8.8", 10, "timeout")
        assert r["status"] == "FAILED"

    def test_error_result_has_error_message(self):
        r = _error_result("8.8.8.8", 10, "host unreachable")
        assert r["error"] == "host unreachable"

    def test_error_result_has_all_required_keys(self):
        required = [
            "test_type", "status", "host", "packets_sent",
            "packet_loss_pct", "rtt_avg_ms", "throughput_mbps",
            "timestamp", "error", "raw_output"
        ]
        r = _error_result("8.8.8.8", 10, "test error")
        for key in required:
            assert key in r, f"Missing key: {key}"

    def test_garbage_output_returns_failed(self):
        r = _parse_ping_output(SAMPLE_GARBAGE, "8.8.8.8", 10)
        assert r["status"] == "FAILED"
