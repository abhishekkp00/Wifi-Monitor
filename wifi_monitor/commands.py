"""
commands.py — One function per CLI subcommand. All I/O here.
"""
from __future__ import annotations
import csv, json, os, signal, sys
from datetime import datetime

from wifi_monitor.config          import get_cfg
from wifi_monitor.ping_test       import run_ping
from wifi_monitor.throughput_test import run_throughput
from wifi_monitor.wifi_info       import get_wifi_info
from wifi_monitor.storage         import save_result, fetch_recent
from wifi_monitor.report          import (
    ping_summary, throughput_summary, combined_summary,
    format_ping_summary, format_throughput_summary,
)
from wifi_monitor.scheduler  import start_scheduler, stop_scheduler
from wifi_monitor.logger     import logger

SEP = "─" * 62  # UI only


def cmd_ping(args) -> int:
    print(f"\n[ping] host={args.host}  count={args.count}  interval={args.interval}s")
    print(SEP)
    r = run_ping(host=args.host, count=args.count, interval=args.interval)
    if r["status"] == "SUCCESS":
        print(f"  RTT avg/min/max : {r['rtt_avg_ms']} / {r['rtt_min_ms']} / {r['rtt_max_ms']} ms")
        print(f"  Packet loss     : {r['packet_loss_pct']} %")
        print(f"  Received        : {r['packets_received']} / {r['packets_sent']}")
    else:
        print(f"  Status  : {r['status']}")
        print(f"  Error   : {r.get('error_message')}")
    if not getattr(args, "no_save", False):
        save_result(r); print("\n  Saved.")
    print(SEP)
    return 0 if r["status"] == "SUCCESS" else 1


def cmd_throughput(args) -> int:
    print(f"\n[throughput] server={args.server}  dur={args.duration}s  proto={args.protocol}")
    print(SEP)
    r = run_throughput(server=args.server, duration=args.duration,
                       protocol=args.protocol,
                       bandwidth=getattr(args, "bandwidth", None), port=args.port)
    if r["status"] == "SUCCESS":
        print(f"  Throughput : {r.get('throughput_mbps')} Mbps")
        if r.get("jitter_ms") is not None:
            print(f"  Jitter     : {r['jitter_ms']} ms")
    else:
        print(f"  Status  : {r['status']}")
        print(f"  Error   : {r.get('error_message')}")
    if not getattr(args, "no_save", False):
        save_result(r); print("\n  Saved.")
    print(SEP)
    return 0 if r["status"] == "SUCCESS" else 1


def cmd_wifi_info(args) -> int:
    print(f"\n[wifi-info]"); print(SEP)
    info = get_wifi_info()
    if info.get("available"):
        for k in ("interface","ssid","ip_address","gateway"):
            print(f"  {k:<12}: {info.get(k,'N/A')}")
    else:
        print(f"  Unavailable: {info.get('error')}")
    print(SEP); return 0


def cmd_run_suite(args) -> int:
    print(f"\n[run-suite]"); print(SEP)
    ping_rc = cmd_ping(args)
    tp_rc   = cmd_throughput(args)
    print(f"\n[suite summary]"); print(SEP)
    s = combined_summary()
    print("  PING\n" + format_ping_summary(s["ping"]))
    print("\n  THROUGHPUT\n" + format_throughput_summary(s["throughput"]))
    print(SEP)
    return 0 if ping_rc == 0 and tp_rc == 0 else 1


def cmd_report(args) -> int:
    print(f"\n[report]  last={args.last}  type={args.test_type}"); print(SEP)
    if args.test_type in ("ping", "all"):
        print("  PING SUMMARY")
        print(format_ping_summary(ping_summary(limit=args.last))); print()
    if args.test_type in ("throughput", "all"):
        print("  THROUGHPUT SUMMARY")
        print(format_throughput_summary(throughput_summary(limit=args.last))); print()
    print(SEP); return 0


def cmd_export(args) -> int:
    rows = fetch_recent(limit=args.last)
    if not rows: print("  No data."); return 2
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = args.output or os.path.join("data", f"export_{ts}.{args.format}")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if args.format == "csv":
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, default=str)
    print(f"\n  Exported {len(rows)} rows → {path}"); return 0


def cmd_schedule(args) -> int:
    interval = args.interval
    print(f"\n[scheduler] running every {interval}s  |  Ctrl+C to stop")
    t = start_scheduler(interval=interval)
    def _handle_exit(sig, frame):
        print("\n[scheduler] stopping..."); stop_scheduler(); sys.exit(0)
    signal.signal(signal.SIGINT, _handle_exit)
    t.join()
    return 0


def cmd_dashboard(args) -> int:
    from dashboard.app import create_app
    host  = args.host
    port  = args.port
    debug = args.debug
    app   = create_app()
    print(f"\n[dashboard] http://{host}:{port}  |  Ctrl+C to stop")
    app.run(host=host, port=port, debug=debug)
    return 0