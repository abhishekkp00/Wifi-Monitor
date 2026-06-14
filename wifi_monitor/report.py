"""
report.py
---------
Pure computation — no print(), no magic numbers.
All thresholds from config via get_cfg().
"""
from __future__ import annotations
import sqlite3
from wifi_monitor.storage import fetch_recent
from wifi_monitor.config  import get_cfg

LOSS_WARN_PCT:   float = get_cfg("thresholds", "loss_warn_pct",        2.0)
THROUGHPUT_WARN: float = get_cfg("thresholds", "throughput_warn_mbps", 10.0)
RTT_WARN_MS:     float = get_cfg("thresholds", "rtt_warn_ms",          100.0)
RTT_POOR_MS:     float = get_cfg("thresholds", "rtt_poor_ms",          200.0)


def _safe_avg(vals): c=[v for v in vals if v is not None]; return round(sum(c)/len(c),3) if c else None
def _safe_min(vals): c=[v for v in vals if v is not None]; return round(min(c),3) if c else None
def _safe_max(vals): c=[v for v in vals if v is not None]; return round(max(c),3) if c else None
def _fmt(v): return "N/A" if v is None else f"{v:.3f}"


def _ping_health(avg_loss):
    if avg_loss is None:            return "UNKNOWN"
    if avg_loss >= 10.0:            return "POOR"
    if avg_loss >= LOSS_WARN_PCT:   return "DEGRADED"
    return "GOOD"


def _throughput_health(avg_mbps):
    if avg_mbps is None:            return "NO DATA"
    if avg_mbps < THROUGHPUT_WARN:  return "LOW"
    return "GOOD"


def _rtt_health(avg_rtt):
    if avg_rtt is None:         return "UNKNOWN"
    if avg_rtt >= RTT_POOR_MS:  return "POOR"
    if avg_rtt >= RTT_WARN_MS:  return "HIGH"
    return "GOOD"


def ping_summary(limit=None, conn=None):
    if limit is None: limit = get_cfg("report", "default_last", 20)
    rows    = fetch_recent(limit=limit, test_type="ping", conn=conn)
    if not rows: return {"total_runs": 0, "health": "NO DATA"}
    success = [r for r in rows if r.get("status") == "SUCCESS"]
    failed  = [r for r in rows if r.get("status") != "SUCCESS"]
    avg_loss = _safe_avg([r.get("packet_loss_pct") for r in rows])
    avg_rtt  = _safe_avg([r.get("rtt_avg_ms") for r in success])
    return {
        "total_runs":   len(rows),
        "success_runs": len(success),
        "failed_runs":  len(failed),
        "avg_rtt_ms":   avg_rtt,
        "min_rtt_ms":   _safe_min([r.get("rtt_min_ms") for r in success]),
        "max_rtt_ms":   _safe_max([r.get("rtt_max_ms") for r in success]),
        "avg_loss_pct": avg_loss,
        "max_loss_pct": _safe_max([r.get("packet_loss_pct") for r in rows]),
        "health":       _ping_health(avg_loss),
        "rtt_health":   _rtt_health(avg_rtt),
    }


def throughput_summary(limit=None, conn=None):
    if limit is None: limit = get_cfg("report", "default_last", 20)
    rows    = fetch_recent(limit=limit, test_type="throughput", conn=conn)
    if not rows: return {"total_runs": 0, "health": "NO DATA"}
    success  = [r for r in rows if r.get("status") == "SUCCESS"]
    failed   = [r for r in rows if r.get("status") != "SUCCESS"]
    avg_mbps = _safe_avg([r.get("throughput_mbps") for r in success])
    return {
        "total_runs":    len(rows),
        "success_runs":  len(success),
        "failed_runs":   len(failed),
        "avg_mbps":      avg_mbps,
        "min_mbps":      _safe_min([r.get("throughput_mbps") for r in success]),
        "max_mbps":      _safe_max([r.get("throughput_mbps") for r in success]),
        "avg_jitter_ms": _safe_avg([r.get("jitter_ms") for r in success]),
        "protocols_used": list({r.get("protocol") for r in rows if r.get("protocol")}),
        "health":        _throughput_health(avg_mbps),
    }


def combined_summary(limit=None, conn=None):
    return {
        "ping":       ping_summary(limit=limit, conn=conn),
        "throughput": throughput_summary(limit=limit, conn=conn),
    }


def format_ping_summary(s):
    if s.get("total_runs", 0) == 0: return "  No ping data yet.\n"
    return "\n".join([
        f"  Runs     : {s['success_runs']} ok / {s['failed_runs']} failed / {s['total_runs']} total",
        f"  Avg RTT  : {_fmt(s.get('avg_rtt_ms'))} ms",
        f"  Min/Max  : {_fmt(s.get('min_rtt_ms'))} / {_fmt(s.get('max_rtt_ms'))} ms",
        f"  Avg Loss : {_fmt(s.get('avg_loss_pct'))} %",
        f"  Health   : {s.get('health')} | RTT: {s.get('rtt_health')}",
    ])


def format_throughput_summary(s):
    if s.get("total_runs", 0) == 0: return "  No throughput data yet.\n"
    proto = ", ".join(sorted(s.get("protocols_used") or [])) or "N/A"
    return "\n".join([
        f"  Runs       : {s['success_runs']} ok / {s['failed_runs']} failed / {s['total_runs']} total",
        f"  Avg / Min / Max : {_fmt(s.get('avg_mbps'))} / {_fmt(s.get('min_mbps'))} / {_fmt(s.get('max_mbps'))} Mbps",
        f"  Avg Jitter : {_fmt(s.get('avg_jitter_ms'))} ms",
        f"  Protocol(s): {proto}",
        f"  Health     : {s.get('health')}",
    ])