"""
test_report.py
--------------
Unit tests for report.py using an in-memory SQLite DB.
All test data is in named factory constants at the top — no inline magic numbers.
"""

import sqlite3
import pytest
from wifi_monitor.storage import init_db, save_result
from wifi_monitor.report  import (
    ping_summary, throughput_summary,
    format_ping_summary, format_throughput_summary,
    LOSS_WARN_PCT, THROUGHPUT_WARN,
)

# ── Test data factories ────────────────────────────────────────────────────
# Named constants — test data, not business logic. Correct pattern.

GOOD_PING = dict(
    test_type="ping", status="SUCCESS", host="8.8.8.8",
    packets_sent=10, packets_received=10, packet_loss_pct=0.0,
    rtt_min_ms=10.0, rtt_avg_ms=15.0, rtt_max_ms=22.0,
    timestamp="2026-06-14T10:00:00",
)
DEGRADED_PING = dict(
    test_type="ping", status="SUCCESS", host="8.8.8.8",
    packets_sent=10, packets_received=97, packet_loss_pct=3.0,
    rtt_min_ms=30.0, rtt_avg_ms=80.0, rtt_max_ms=200.0,
    timestamp="2026-06-14T10:01:00",
)
FAILED_PING = dict(
    test_type="ping", status="HOST_UNREACHABLE", host="1.2.3.4",
    packets_sent=10, packets_received=0, packet_loss_pct=100.0,
    timestamp="2026-06-14T10:02:00",
)
GOOD_THROUGHPUT = dict(
    test_type="throughput", status="SUCCESS", server="192.168.1.10",
    protocol="tcp", duration_seconds=10,
    throughput_mbps=85.5, jitter_ms=None,
    timestamp="2026-06-14T10:03:00",
)
LOW_THROUGHPUT = dict(
    test_type="throughput", status="SUCCESS", server="192.168.1.10",
    protocol="udp", duration_seconds=10,
    throughput_mbps=5.0, jitter_ms=3.2,
    timestamp="2026-06-14T10:04:00",
)


@pytest.fixture
def mem_conn():
    """In-memory SQLite connection — isolated per test, no disk writes."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn=conn)
    yield conn
    conn.close()


# ── ping_summary ───────────────────────────────────────────────────────────

def test_ping_summary_empty(mem_conn):
    s = ping_summary(limit=10, conn=mem_conn)
    assert s["total_runs"] == 0
    assert s["health"] == "NO DATA"


def test_ping_summary_good_health(mem_conn):
    save_result(GOOD_PING, conn=mem_conn)
    s = ping_summary(limit=10, conn=mem_conn)
    assert s["total_runs"]   == 1
    assert s["success_runs"] == 1
    assert s["failed_runs"]  == 0
    assert s["avg_rtt_ms"]   == 15.0
    assert s["avg_loss_pct"] == 0.0
    assert s["health"]       == "GOOD"


def test_ping_summary_degraded_health(mem_conn):
    # packet loss is above LOSS_WARN_PCT threshold (from config)
    save_result(DEGRADED_PING, conn=mem_conn)
    s = ping_summary(limit=10, conn=mem_conn)
    assert s["avg_loss_pct"] > LOSS_WARN_PCT
    assert s["health"] == "DEGRADED"


def test_ping_summary_failed_run_counted(mem_conn):
    save_result(GOOD_PING,   conn=mem_conn)
    save_result(FAILED_PING, conn=mem_conn)
    s = ping_summary(limit=10, conn=mem_conn)
    assert s["total_runs"]   == 2
    assert s["failed_runs"]  == 1
    assert s["success_runs"] == 1


# ── throughput_summary ─────────────────────────────────────────────────────

def test_throughput_summary_empty(mem_conn):
    s = throughput_summary(limit=10, conn=mem_conn)
    assert s["total_runs"] == 0
    assert s["health"] == "NO DATA"


def test_throughput_summary_good(mem_conn):
    save_result(GOOD_THROUGHPUT, conn=mem_conn)
    s = throughput_summary(limit=10, conn=mem_conn)
    assert s["avg_mbps"]  == 85.5
    assert s["health"]    == "GOOD"
    assert "tcp" in s["protocols_used"]


def test_throughput_summary_low(mem_conn):
    save_result(LOW_THROUGHPUT, conn=mem_conn)
    s = throughput_summary(limit=10, conn=mem_conn)
    assert s["avg_mbps"] < THROUGHPUT_WARN
    assert s["health"] == "LOW"


# ── formatters ────────────────────────────────────────────────────────────

def test_format_ping_no_data():
    out = format_ping_summary({"total_runs": 0, "health": "NO DATA"})
    assert "No ping data" in out


def test_format_ping_with_data(mem_conn):
    save_result(GOOD_PING, conn=mem_conn)
    s   = ping_summary(limit=10, conn=mem_conn)
    out = format_ping_summary(s)
    assert "Avg RTT" in out
    assert "Health" in out
    assert "GOOD"   in out


def test_format_throughput_no_data():
    out = format_throughput_summary({"total_runs": 0, "health": "NO DATA"})
    assert "No throughput data" in out