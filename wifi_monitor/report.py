from wifi_monitor.storage import (
    fetch_recent,
    fetch_ping_stats,
    fetch_throughput_stats,
    count_rows
)

def _divider(char="─", width=60):
    return char * width

def _fmt(value, suffix="", decimals=2, na="N/A"):
    if value is None:
        return na
    return f"{value:.{decimals}f}{suffix}"

def _quality_rating(avg_rtt_ms, avg_loss_pct):
    if avg_loss_pct > 5:
        return "POOR    (loss > 5%)"
    if avg_loss_pct > 1:
        return "FAIR    (loss 1-5%)"
    if avg_rtt_ms > 150:
        return "FAIR    (latency > 150ms)"
    if avg_rtt_ms > 50:
        return "GOOD    (latency 50-150ms)"
    return "EXCELLENT (low latency, minimal loss)"

def print_summary(last_n=10, test_type="all"):
    total = count_rows()
    print()
    print(_divider("═"))
    print("  Wi-Fi Monitor — Test Report")
    print(_divider("═"))
    print(f"  Total records in database : {total}")
    print(_divider())

    if test_type in ("ping", "all"):
        ping_stats = fetch_ping_stats(last_n=last_n)
        print()
        print("  PING RESULTS")
        print(_divider("─", 40))
        if ping_stats and ping_stats["total_runs"] > 0:
            print(f"  Runs analysed  : {ping_stats['total_runs']}")
            print(f"  Avg RTT        : {_fmt(ping_stats['avg_rtt_ms'], ' ms')}")
            print(f"  Best RTT       : {_fmt(ping_stats['best_rtt_ms'], ' ms')}")
            print(f"  Worst RTT      : {_fmt(ping_stats['worst_rtt_ms'], ' ms')}")
            print(f"  Avg loss       : {_fmt(ping_stats['avg_loss_pct'], '%')}")
            print(f"  Worst loss     : {_fmt(ping_stats['max_loss_pct'], '%')}")
            avg_rtt  = ping_stats["avg_rtt_ms"]  or 999
            avg_loss = ping_stats["avg_loss_pct"] or 0
            print()
            print(f"  Quality        : {_quality_rating(avg_rtt, avg_loss)}")
        else:
            print("  No successful ping results found.")

    if test_type in ("throughput", "all"):
        tp_list = fetch_throughput_stats(last_n=last_n)
        print()
        print("  THROUGHPUT RESULTS")
        print(_divider("─", 40))
        if tp_list:
            for tp in tp_list:
                print()
                print(f"  Protocol       : {tp.get('protocol','UNKNOWN')}")
                print(f"  Runs analysed  : {tp['total_runs']}")
                print(f"  Avg throughput : {_fmt(tp['avg_throughput_mbps'], ' Mbps')}")
                print(f"  Best           : {_fmt(tp['best_throughput_mbps'], ' Mbps')}")
                print(f"  Worst          : {_fmt(tp['worst_throughput_mbps'], ' Mbps')}")
                if tp.get("avg_jitter_ms") is not None:
                    print(f"  Avg jitter     : {_fmt(tp['avg_jitter_ms'], ' ms')}")
                if tp.get("avg_loss_pct") is not None:
                    print(f"  Avg loss       : {_fmt(tp['avg_loss_pct'], '%')}")
        else:
            print("  No successful throughput results found.")

    print()
    print(_divider("─", 40))
    print(f"  LAST {last_n} RUNS (most recent first)")
    print(_divider("─", 40))
    print_recent(last_n=last_n, test_type=test_type)
    print()
    print(_divider("═"))
    print()

def print_recent(last_n=10, test_type="all"):
    rows = fetch_recent(last_n=last_n, test_type=test_type)
    if not rows:
        print("  No results found.")
        return
    print(f"  {'#':<4} {'Timestamp':<22} {'Type':<12} {'Status':<8} {'Key Metric'}")
    print("  " + _divider("─", 66))
    for i, row in enumerate(rows, start=1):
        ts     = (row["timestamp"] or "")[:19]
        ttype  = row["test_type"] or "?"
        status = row["status"] or "?"
        if ttype == "ping":
            metric = f"RTT {_fmt(row['rtt_avg_ms'], ' ms')}, Loss {_fmt(row['packet_loss_pct'], '%')}"
        elif ttype == "throughput":
            metric = f"{_fmt(row['throughput_mbps'], ' Mbps')} {row['protocol'] or ''}"
        else:
            metric = row["error"] or ""
        print(f"  {i:<4} {ts:<22} {ttype:<12} {status:<8} {metric}")
