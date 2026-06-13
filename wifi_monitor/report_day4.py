
# ============================================================
# DAY 4 — report.py
# Project: Wi-Fi Throughput & Latency Monitor CLI
# File: wifi_monitor/report.py
# ============================================================

"""
WHAT THIS FILE DOES
--------------------
Reads from SQLite via storage.py and prints human-readable
summaries to the terminal.

Two modes:
  1. print_summary()   — called by `main.py report` command
  2. print_recent()    — called to show last N raw rows

WHY SEPARATE FROM storage.py?
-------------------------------
Single Responsibility Principle (SRP) — one of the OOP
design principles Candela interviewers ask about.
storage.py = data access only.
report.py  = presentation/formatting only.
They do not know about each other directly.

DESIGN CHOICE: No pandas dependency
-------------------------------------
We use only Python standard library here (sqlite3 + string
formatting). This keeps requirements.txt minimal and makes
the tool run anywhere without heavy installs.
"""

from wifi_monitor.storage import (
    fetch_recent,
    fetch_ping_stats,
    fetch_throughput_stats,
    count_rows
)


# ── Formatting helpers ──────────────────────────────────────

def _divider(char: str = "─", width: int = 60) -> str:
    return char * width


def _fmt(value, suffix: str = "", decimals: int = 2, na: str = "N/A") -> str:
    """
    Safely format a number for display.
    Returns na string if value is None.

    Examples:
        _fmt(14.234, suffix=" ms")     -> "14.23 ms"
        _fmt(None,   suffix=" ms")     -> "N/A"
        _fmt(0.0,    suffix=" Mbps")   -> "0.00 Mbps"
    """
    if value is None:
        return na
    return f"{value:.{decimals}f}{suffix}"


# ── Main summary printer ────────────────────────────────────

def print_summary(last_n: int = 10, test_type: str = "all") -> None:
    """
    Print a formatted summary of recent test results.
    Called by main.py when user runs:
        python -m wifi_monitor.main report --last 20

    Shows:
    - Database overview (total rows)
    - Ping aggregate stats (avg RTT, worst loss, etc.)
    - Throughput aggregate stats (by TCP/UDP)
    - Last N raw rows as a mini table
    """
    total = count_rows()
    print()
    print(_divider("═"))
    print("  Wi-Fi Monitor — Test Report")
    print(_divider("═"))
    print(f"  Total records in database : {total}")
    print(_divider())

    # ── Ping section ─────────────────────────────────────────
    if test_type in ("ping", "all"):
        ping_stats = fetch_ping_stats(last_n=last_n)
        print()
        print("  PING RESULTS")
        print(_divider("─", 40))
        if ping_stats and ping_stats["total_runs"] > 0:
            print(f"  Runs analysed  : {ping_stats['total_runs']}")
            print(f"  Avg RTT        : {_fmt(ping_stats['avg_rtt_ms'],  ' ms')}")
            print(f"  Best RTT       : {_fmt(ping_stats['best_rtt_ms'], ' ms')}")
            print(f"  Worst RTT      : {_fmt(ping_stats['worst_rtt_ms'],' ms')}")
            print(f"  Avg loss       : {_fmt(ping_stats['avg_loss_pct'], '%')}")
            print(f"  Worst loss     : {_fmt(ping_stats['max_loss_pct'], '%')}")

            # Quality rating — simple but interview-friendly
            avg_rtt  = ping_stats["avg_rtt_ms"]  or 999
            avg_loss = ping_stats["avg_loss_pct"] or 0
            print()
            print(f"  Quality        : {_quality_rating(avg_rtt, avg_loss)}")
        else:
            print("  No successful ping results found.")

    # ── Throughput section ────────────────────────────────────
    if test_type in ("throughput", "all"):
        tp_stats_list = fetch_throughput_stats(last_n=last_n)
        print()
        print("  THROUGHPUT RESULTS")
        print(_divider("─", 40))
        if tp_stats_list:
            for tp in tp_stats_list:
                proto = tp.get("protocol", "UNKNOWN")
                print()
                print(f"  Protocol       : {proto}")
                print(f"  Runs analysed  : {tp['total_runs']}")
                print(f"  Avg throughput : {_fmt(tp['avg_throughput_mbps'], ' Mbps')}")
                print(f"  Best           : {_fmt(tp['best_throughput_mbps'],' Mbps')}")
                print(f"  Worst          : {_fmt(tp['worst_throughput_mbps'],' Mbps')}")
                if tp.get("avg_jitter_ms") is not None:
                    print(f"  Avg jitter     : {_fmt(tp['avg_jitter_ms'], ' ms')}")
                if tp.get("avg_loss_pct") is not None:
                    print(f"  Avg loss       : {_fmt(tp['avg_loss_pct'], '%')}")
        else:
            print("  No successful throughput results found.")

    # ── Recent raw rows ───────────────────────────────────────
    print()
    print(_divider("─", 40))
    print(f"  LAST {last_n} RUNS (most recent first)")
    print(_divider("─", 40))
    print_recent(last_n=last_n, test_type=test_type)

    print()
    print(_divider("═"))
    print()


def print_recent(last_n: int = 10, test_type: str = "all") -> None:
    """
    Print a mini table of raw recent test rows.
    Useful for a quick glance at what was just recorded.

    Output format:
    ─────────────────────────────────────────────────────────────
     #  | Timestamp           | Type       | Status  | Key Metric
    ─────────────────────────────────────────────────────────────
     1  | 2026-06-13T08:30:00 | ping       | SUCCESS | RTT 14.2ms, Loss 0%
     2  | 2026-06-13T08:29:50 | throughput | SUCCESS | 91.3 Mbps TCP
    """
    rows = fetch_recent(last_n=last_n, test_type=test_type)

    if not rows:
        print("  No results found.")
        return

    header = f"  {'#':<4} {'Timestamp':<22} {'Type':<12} {'Status':<8} {'Key Metric'}"
    print(header)
    print("  " + _divider("─", 72))

    for i, row in enumerate(rows, start=1):
        ts        = (row["timestamp"] or "")[:19]   # trim microseconds
        ttype     = row["test_type"] or "?"
        status    = row["status"] or "?"

        # Pick the most relevant metric per test type
        if ttype == "ping":
            rtt  = _fmt(row["rtt_avg_ms"],     " ms")
            loss = _fmt(row["packet_loss_pct"], "%")
            metric = f"RTT {rtt}, Loss {loss}"
        elif ttype == "throughput":
            bw    = _fmt(row["throughput_mbps"], " Mbps")
            proto = row["protocol"] or ""
            metric = f"{bw} {proto}"
        else:
            metric = row["error"] or ""

        print(f"  {i:<4} {ts:<22} {ttype:<12} {status:<8} {metric}")


# ── Quality rating helper ───────────────────────────────────

def _quality_rating(avg_rtt_ms: float, avg_loss_pct: float) -> str:
    """
    Simple rule-based Wi-Fi quality rating.
    Based on general industry thresholds for enterprise Wi-Fi.

    Interview talking point:
    "These thresholds are based on general Wi-Fi performance
    benchmarks. In a production system like LANforge, these
    would be configurable pass/fail criteria per test plan."
    """
    if avg_loss_pct > 5:
        return "POOR    (loss > 5% — significant connectivity issues)"
    if avg_loss_pct > 1:
        return "FAIR    (loss 1-5% — degraded, investigate interference)"
    if avg_rtt_ms > 150:
        return "FAIR    (high latency > 150ms — check routing or load)"
    if avg_rtt_ms > 50:
        return "GOOD    (latency 50-150ms — acceptable for most apps)"
    return "EXCELLENT (low latency, minimal loss — strong Wi-Fi)"
