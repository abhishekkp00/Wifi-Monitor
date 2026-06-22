"""
storage.py — SQLite persistence layer for wifi-monitor.

All public functions accept an optional `conn` parameter.
- Production: pass nothing → function creates + closes its own connection.
- Tests:       pass the fixture connection → function uses it, never closes it.
"""

import sqlite3
import os


def fetch_chart_data(limit: int = 20, test_type: str | None = None, conn: sqlite3.Connection = None) -> list:
    _own = conn is None
    c = conn or _open()
    try:
        if test_type:
            rows = c.execute(
                """
                SELECT timestamp, test_type, rtt_avg_ms, packet_loss_pct, throughput_mbps, jitter_ms, signal_strength
                FROM test_runs
                WHERE test_type = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (test_type, limit)
            ).fetchall()
        else:
            rows = c.execute(
                """
                SELECT timestamp, test_type, rtt_avg_ms, packet_loss_pct, throughput_mbps, jitter_ms, signal_strength
                FROM test_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
        res = [dict(row) for row in rows]
        res.reverse()
        return res
    finally:
        if _own:
            c.close()

def count_runs(conn: sqlite3.Connection = None) -> dict:
    _own = conn is None
    c = conn or _open()
    try:
        total = c.execute("SELECT COUNT(*) FROM test_runs").fetchone()[0]
        success = c.execute("SELECT COUNT(*) FROM test_runs WHERE status = 'SUCCESS'").fetchone()[0]
        return {
            "total": total,
            "success_count": success
        }
    finally:
        if _own:
            c.close()

DB_PATH = os.environ.get(
    "WIFI_MONITOR_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "results.db")
)


def _open() -> sqlite3.Connection:
    """Create a new file-based connection (production use)."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db(conn: sqlite3.Connection = None) -> None:
    _own = conn is None
    c = conn or _open()
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS test_runs (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp           TEXT,
                test_type           TEXT,
                status              TEXT DEFAULT 'UNKNOWN',
                host                TEXT,
                server              TEXT,
                interface           TEXT,
                ssid                TEXT,
                ip_address          TEXT,
                local_ip            TEXT,
                remote_ip           TEXT,
                protocol            TEXT,
                duration_seconds    INTEGER,
                bandwidth_target    TEXT,
                packets_sent        INTEGER,
                packets_received    INTEGER,
                packet_loss_pct     REAL,
                rtt_min_ms          REAL,
                rtt_avg_ms          REAL,
                rtt_max_ms          REAL,
                rtt_mdev_ms         REAL,
                throughput_mbps     REAL,
                upload_mbps         REAL,
                jitter_ms           REAL,
                iperf_version       TEXT,
                raw_output          TEXT,
                error               TEXT,
                notes               TEXT,
                signal_strength     INTEGER
            )
        """)
        # migrate existing DBs — safe no-op if column already exists
        try:
            c.execute("ALTER TABLE test_runs ADD COLUMN upload_mbps REAL")
        except Exception:
            pass
        try:
            c.execute("ALTER TABLE test_runs ADD COLUMN signal_strength INTEGER")
        except Exception:
            pass
        c.commit()
    finally:
        if _own:
            c.close()


def save_result(result: dict, conn: sqlite3.Connection = None) -> int:
    _own = conn is None
    c = conn or _open()
    try:
        cursor = c.execute(
            """
            INSERT INTO test_runs (
                timestamp, test_type, status,
                host, server, interface, ssid, ip_address,
                local_ip, remote_ip,
                protocol, duration_seconds, bandwidth_target,
                packets_sent, packets_received, packet_loss_pct,
                rtt_min_ms, rtt_avg_ms, rtt_max_ms, rtt_mdev_ms,
                throughput_mbps, upload_mbps, jitter_ms,
                iperf_version, raw_output, error, notes, signal_strength
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                result.get("timestamp"),          result.get("test_type"),
                result.get("status", "UNKNOWN"),
                result.get("host"),               result.get("server"),
                result.get("interface"),          result.get("ssid"),
                result.get("ip_address"),         result.get("local_ip"),
                result.get("remote_ip"),          result.get("protocol"),
                result.get("duration_seconds"),   result.get("bandwidth_target"),
                result.get("packets_sent"),       result.get("packets_received"),
                result.get("packet_loss_pct"),
                result.get("rtt_min_ms"),         result.get("rtt_avg_ms"),
                result.get("rtt_max_ms"),         result.get("rtt_mdev_ms"),
                result.get("throughput_mbps"),    result.get("upload_mbps"),
                result.get("jitter_ms"),
                result.get("iperf_version"),      result.get("raw_output"),
                result.get("error"),              result.get("notes"),
                result.get("signal_strength"),
            )
        )
        c.commit()
        return cursor.lastrowid
    finally:
        if _own:
            c.close()


def fetch_recent(limit: int = 20, test_type: str = None,
                 conn: sqlite3.Connection = None) -> list:
    _own = conn is None
    c = conn or _open()
    try:
        if test_type:
            rows = c.execute(
                "SELECT * FROM test_runs WHERE test_type=? ORDER BY id DESC LIMIT ?",
                (test_type, limit)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM test_runs ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if _own:
            c.close()


def count_rows(conn: sqlite3.Connection = None) -> int:
    _own = conn is None
    c = conn or _open()
    try:
        return c.execute("SELECT COUNT(*) FROM test_runs").fetchone()[0]
    finally:
        if _own:
            c.close()


def clear_all(confirm: bool = False, conn: sqlite3.Connection = None) -> None:
    if not confirm:
        raise ValueError("Pass confirm=True to clear all data.")
    _own = conn is None
    c = conn or _open()
    try:
        c.execute("DELETE FROM test_runs")
        c.commit()
    finally:
        if _own:
            c.close()


def get_ping_stats(conn: sqlite3.Connection = None) -> dict | None:
    _own = conn is None
    c = conn or _open()
    try:
        row = c.execute("""
            SELECT
                ROUND(AVG(rtt_avg_ms), 3)      AS avg_rtt,
                ROUND(MIN(rtt_min_ms), 3)      AS min_rtt,
                ROUND(MAX(rtt_max_ms), 3)      AS max_rtt,
                ROUND(AVG(packet_loss_pct), 2) AS avg_loss,
                COUNT(*)                        AS total_runs
            FROM test_runs
            WHERE test_type = 'ping' AND status = 'SUCCESS'
        """).fetchone()
        if row and row["total_runs"] and row["total_runs"] > 0:
            return dict(row)
        return None
    finally:
        if _own:
            c.close()
