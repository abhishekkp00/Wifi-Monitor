"""
test_storage_day4.py — Storage layer tests using dependency injection.
Defaults live in one place. Tests only override what they care about.
"""

import sqlite3
import pytest
from wifi_monitor.storage import (
    init_db, save_result, fetch_recent,
    count_rows, clear_all, get_ping_stats,
)


# ── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture()
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn=conn)
    yield conn
    conn.close()


# ── Factories — defaults live here, tests override only what matters ──────────

PING_DEFAULTS = dict(
    test_type        = "ping",
    status           = "SUCCESS",
    host             = "8.8.8.8",
    timestamp        = "2026-06-13T10:00:00",
    packets_sent     = 10,
    packets_received = 10,
    packet_loss_pct  = 0.0,
    rtt_min_ms       = 10.1,
    rtt_avg_ms       = 14.5,
    rtt_max_ms       = 22.7,
    rtt_mdev_ms      = 3.1,
    throughput_mbps  = None,
    jitter_ms        = None,
    raw_output       = "10 packets transmitted, 10 received, 0% packet loss",
    error            = None,
    notes            = None,
)

THROUGHPUT_DEFAULTS = dict(
    test_type        = "throughput",
    status           = "SUCCESS",
    server           = "192.168.1.10",
    timestamp        = "2026-06-13T10:05:00",
    protocol         = "TCP",
    duration_seconds = 10,
    throughput_mbps  = 84.5,
    jitter_ms        = None,
    packet_loss_pct  = None,
    rtt_avg_ms       = None,
    raw_output       = "[ ID] Interval       Transfer     Bitrate",
    error            = None,
    notes            = None,
)


def make_ping(db, **overrides):
    """Insert a ping result. Only pass fields you want to change."""
    result = {**PING_DEFAULTS, **overrides}
    return save_result(result, conn=db)


def make_throughput(db, **overrides):
    """Insert a throughput result. Only pass fields you want to change."""
    result = {**THROUGHPUT_DEFAULTS, **overrides}
    return save_result(result, conn=db)


# ── TestInitDB ────────────────────────────────────────────────────────────────

class TestInitDB:

    def test_init_db_creates_table(self, db):
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_runs'"
        ).fetchall()
        assert len(tables) == 1

    def test_table_has_expected_columns(self, db):
        cols = [row[1] for row in db.execute("PRAGMA table_info(test_runs)").fetchall()]
        for col in ["id", "timestamp", "test_type", "status", "rtt_avg_ms", "throughput_mbps"]:
            assert col in cols


# ── TestSaveResult ────────────────────────────────────────────────────────────

class TestSaveResult:

    def test_save_ping_result_inserts_row(self, db):
        assert make_ping(db) == 1

    def test_save_throughput_result_inserts_row(self, db):
        assert make_throughput(db) == 1

    def test_count_rows_increments(self, db):
        assert count_rows(conn=db) == 0
        make_ping(db)
        assert count_rows(conn=db) == 1
        make_throughput(db)
        assert count_rows(conn=db) == 2

    def test_ping_metrics_stored_correctly(self, db):
        make_ping(db)
        row = db.execute("SELECT * FROM test_runs WHERE id=1").fetchone()
        assert row["rtt_avg_ms"]       == PING_DEFAULTS["rtt_avg_ms"]
        assert row["packet_loss_pct"]  == PING_DEFAULTS["packet_loss_pct"]
        assert row["packets_sent"]     == PING_DEFAULTS["packets_sent"]
        assert row["host"]             == PING_DEFAULTS["host"]
        assert row["status"]           == PING_DEFAULTS["status"]

    def test_throughput_metrics_stored_correctly(self, db):
        make_throughput(db)
        row = db.execute("SELECT * FROM test_runs WHERE id=1").fetchone()
        assert row["throughput_mbps"]  == THROUGHPUT_DEFAULTS["throughput_mbps"]
        assert row["protocol"]         == THROUGHPUT_DEFAULTS["protocol"]
        assert row["duration_seconds"] == THROUGHPUT_DEFAULTS["duration_seconds"]
        assert row["server"]           == THROUGHPUT_DEFAULTS["server"]

    def test_ping_jitter_stored_as_null(self, db):
        make_ping(db)
        row = db.execute("SELECT jitter_ms FROM test_runs WHERE id=1").fetchone()
        assert row["jitter_ms"] is None

    def test_failed_result_stored_without_crash(self, db):
        # Only override the fields that make it a failure scenario
        row_id = make_ping(db,
            status = "FAILED",
            host   = "10.0.0.99",
            error  = "host unreachable",
            packet_loss_pct  = 100.0,
            packets_received = 0,
            rtt_min_ms = None,
            rtt_avg_ms = None,
            rtt_max_ms = None,
        )
        assert row_id == 1


# ── TestFetchRecent ───────────────────────────────────────────────────────────

class TestFetchRecent:

    def test_fetch_recent_returns_correct_count(self, db):
        for i in range(5):
            make_ping(db, timestamp=f"2026-06-13T10:0{i}:00")
        assert len(fetch_recent(limit=3, conn=db)) == 3

    def test_fetch_recent_ordered_newest_first(self, db):
        make_ping(db, timestamp="2026-06-13T08:00:00")
        make_ping(db, timestamp="2026-06-13T09:00:00")
        make_ping(db, timestamp="2026-06-13T10:00:00")
        rows = fetch_recent(limit=3, conn=db)
        assert rows[0]["timestamp"] == "2026-06-13T10:00:00"

    def test_fetch_recent_filtered_by_type(self, db):
        make_ping(db)
        make_ping(db)
        make_throughput(db)
        rows = fetch_recent(limit=10, test_type="ping", conn=db)
        assert len(rows) == 2
        assert all(r["test_type"] == "ping" for r in rows)

    def test_fetch_recent_returns_dicts(self, db):
        make_ping(db)
        rows = fetch_recent(limit=1, conn=db)
        assert isinstance(rows[0], dict)


# ── TestClearAll ──────────────────────────────────────────────────────────────

class TestClearAll:

    def test_clear_all_data_empties_table(self, db):
        make_ping(db)
        make_ping(db)
        assert count_rows(conn=db) == 2
        clear_all(confirm=True, conn=db)
        assert count_rows(conn=db) == 0

    def test_clear_without_confirm_raises(self, db):
        with pytest.raises(ValueError):
            clear_all(conn=db)


# ── TestPingStats ─────────────────────────────────────────────────────────────

class TestPingStats:

    def test_ping_stats_returns_none_when_empty(self, db):
        assert get_ping_stats(conn=db) is None

    def test_ping_stats_avg_rtt_correct(self, db):
        make_ping(db, rtt_avg_ms=10.0)
        make_ping(db, rtt_avg_ms=20.0)
        stats = get_ping_stats(conn=db)
        assert stats["avg_rtt"] == 15.0

    def test_ping_stats_excludes_failed_runs(self, db):
        make_ping(db, rtt_avg_ms=10.0, status="SUCCESS")
        make_ping(db, rtt_avg_ms=999.0, status="FAILED")
        stats = get_ping_stats(conn=db)
        assert stats["avg_rtt"] == 10.0

    def test_ping_stats_total_runs_count(self, db):
        make_ping(db)
        make_ping(db)
        make_ping(db)
        stats = get_ping_stats(conn=db)
        assert stats["total_runs"] == 3
