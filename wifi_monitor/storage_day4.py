
# ============================================================
# DAY 4 — storage.py
# Project: Wi-Fi Throughput & Latency Monitor CLI
# File: wifi_monitor/storage.py
# ============================================================

"""
WHAT THIS FILE DOES
--------------------
Handles ALL database operations for the project.
Every test result — ping or throughput — gets saved here.
Later, report.py reads from here to generate summaries.

WHY SQLite?
-----------
- Built into Python standard library (no pip install needed)
- Serverless — no MySQL/PostgreSQL server to run
- Single file database: data/results.db
- Perfect for a CLI tool that runs locally
- Supports full SQL: SELECT, GROUP BY, WHERE, ORDER BY
- Candela interview angle: "I chose SQLite because this is a
  local test automation tool. For a distributed system with
  multiple test nodes, I'd use PostgreSQL."

DATABASE FILE LOCATION
-----------------------
data/results.db  (auto-created on first run)

TABLE: test_runs
-----------------
One row per test execution.
Stores BOTH ping and throughput results in one table.
Fields that don't apply to a test type are stored as NULL.
Example: jitter_ms is NULL for ping rows.
"""

import sqlite3
import os
from typing import List, Dict, Optional

# ── Path setup ──────────────────────────────────────────────
# __file__ = wifi_monitor/storage.py
# We go up one level to project root, then into data/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "results.db")


# ── Table definition ────────────────────────────────────────
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS test_runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT    NOT NULL,
    test_type           TEXT    NOT NULL,
    status              TEXT    NOT NULL,

    -- Network target
    host                TEXT,
    server              TEXT,
    interface           TEXT,
    ssid                TEXT,
    ip_address          TEXT,
    local_ip            TEXT,
    remote_ip           TEXT,

    -- Protocol info
    protocol            TEXT,
    duration_seconds    INTEGER,
    bandwidth_target    TEXT,

    -- Ping metrics
    packets_sent        INTEGER,
    packets_received    INTEGER,
    packet_loss_pct     REAL,
    rtt_min_ms          REAL,
    rtt_avg_ms          REAL,
    rtt_max_ms          REAL,
    rtt_mdev_ms         REAL,

    -- Throughput metrics
    throughput_mbps     REAL,
    jitter_ms           REAL,

    -- Debug and audit
    iperf_version       TEXT,
    raw_output          TEXT,
    error               TEXT,
    notes               TEXT
);
"""

# Index to speed up common queries (report by timestamp, type)
CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_test_runs_timestamp
ON test_runs (timestamp DESC);
"""


# ── Core functions ──────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """
    Open and return a SQLite connection.

    row_factory = sqlite3.Row lets us access columns by name:
        row["rtt_avg_ms"]  instead of  row[15]
    This makes report.py much cleaner.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # access columns by name
    return conn


def init_db() -> None:
    """
    Create the database file and table if they don't exist yet.
    Called once at startup from main.py.
    Safe to call multiple times — CREATE TABLE IF NOT EXISTS.
    """
    conn = get_connection()
    try:
        conn.execute(CREATE_TABLE_SQL)
        conn.execute(CREATE_INDEX_SQL)
        conn.commit()
    finally:
        conn.close()


def save_result(result: dict) -> int:
    """
    Insert one test result dict into test_runs table.
    Works for BOTH ping and throughput results.

    Args:
        result: dict returned by ping_test.py or throughput_test.py

    Returns:
        id (int): the row id of the inserted record

    HOW IT WORKS
    ------------
    We use .get() with None defaults so missing keys
    (e.g., jitter_ms for a ping result) become NULL in SQLite.
    This keeps one table for all test types — clean design.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO test_runs (
                timestamp, test_type, status,
                host, server, interface, ssid, ip_address,
                local_ip, remote_ip,
                protocol, duration_seconds, bandwidth_target,
                packets_sent, packets_received, packet_loss_pct,
                rtt_min_ms, rtt_avg_ms, rtt_max_ms, rtt_mdev_ms,
                throughput_mbps, jitter_ms,
                iperf_version, raw_output, error, notes
            ) VALUES (
                ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?
            )
            """,
            (
                result.get("timestamp"),
                result.get("test_type"),
                result.get("status", "UNKNOWN"),

                result.get("host"),
                result.get("server"),
                result.get("interface"),
                result.get("ssid"),
                result.get("ip_address"),

                result.get("local_ip"),
                result.get("remote_ip"),

                result.get("protocol"),
                result.get("duration_seconds"),
                result.get("bandwidth_target"),

                result.get("packets_sent"),
                result.get("packets_received"),
                result.get("packet_loss_pct"),
                result.get("rtt_min_ms"),
                result.get("rtt_avg_ms"),
                result.get("rtt_max_ms"),
                result.get("rtt_mdev_ms"),

                result.get("throughput_mbps"),
                result.get("jitter_ms"),

                result.get("iperf_version"),
                result.get("raw_output"),
                result.get("error"),
                result.get("notes"),
            )
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def fetch_recent(last_n: int = 10, test_type: str = "all") -> List[sqlite3.Row]:
    """
    Fetch the N most recent test results.

    Args:
        last_n    : how many rows to return
        test_type : "ping", "throughput", or "all"

    Returns:
        List of sqlite3.Row objects (column-name accessible)

    SQL used:
        SELECT * FROM test_runs
        WHERE test_type = ?          -- if filter applied
        ORDER BY timestamp DESC
        LIMIT ?
    """
    conn = get_connection()
    try:
        if test_type == "all":
            rows = conn.execute(
                "SELECT * FROM test_runs ORDER BY timestamp DESC LIMIT ?",
                (last_n,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM test_runs WHERE test_type = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (test_type, last_n)
            ).fetchall()
        return rows
    finally:
        conn.close()


def fetch_ping_stats(last_n: int = 50) -> Optional[Dict]:
    """
    Aggregate ping statistics for the last N successful ping runs.

    Uses SQL AVG(), MIN(), MAX() for efficiency.
    Returns None if no ping data exists yet.

    SQL concept used: GROUP BY with aggregate functions.
    Interview tip: explain this as "server-side aggregation —
    let the DB compute averages instead of pulling all rows
    into Python and looping."
    """
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                COUNT(*)            AS total_runs,
                AVG(rtt_avg_ms)     AS avg_rtt_ms,
                MIN(rtt_min_ms)     AS best_rtt_ms,
                MAX(rtt_max_ms)     AS worst_rtt_ms,
                AVG(packet_loss_pct) AS avg_loss_pct,
                MAX(packet_loss_pct) AS max_loss_pct
            FROM test_runs
            WHERE test_type = 'ping'
              AND status = 'SUCCESS'
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (last_n,)
        ).fetchone()

        if row and row["total_runs"] > 0:
            return dict(row)
        return None
    finally:
        conn.close()


def fetch_throughput_stats(last_n: int = 50) -> Optional[Dict]:
    """
    Aggregate throughput statistics.
    Groups by protocol (TCP vs UDP) for separate summaries.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                protocol,
                COUNT(*)                AS total_runs,
                AVG(throughput_mbps)    AS avg_throughput_mbps,
                MAX(throughput_mbps)    AS best_throughput_mbps,
                MIN(throughput_mbps)    AS worst_throughput_mbps,
                AVG(jitter_ms)          AS avg_jitter_ms,
                AVG(packet_loss_pct)    AS avg_loss_pct
            FROM test_runs
            WHERE test_type = 'throughput'
              AND status = 'SUCCESS'
            GROUP BY protocol
            ORDER BY protocol
            """,
        ).fetchall()

        if rows:
            return [dict(r) for r in rows]
        return None
    finally:
        conn.close()


def fetch_all_for_export(test_type: str = "all") -> List[sqlite3.Row]:
    """
    Fetch ALL rows for CSV/JSON export.
    No LIMIT — returns everything in the database.
    """
    conn = get_connection()
    try:
        if test_type == "all":
            return conn.execute(
                "SELECT * FROM test_runs ORDER BY timestamp DESC"
            ).fetchall()
        else:
            return conn.execute(
                "SELECT * FROM test_runs WHERE test_type = ? "
                "ORDER BY timestamp DESC",
                (test_type,)
            ).fetchall()
    finally:
        conn.close()


def count_rows() -> int:
    """Return total number of rows in the database."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) FROM test_runs").fetchone()
        return row[0]
    finally:
        conn.close()


def clear_all_data() -> None:
    """
    Delete all rows. Used in tests only.
    NOT exposed in CLI — prevents accidents.
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM test_runs")
        conn.commit()
    finally:
        conn.close()
