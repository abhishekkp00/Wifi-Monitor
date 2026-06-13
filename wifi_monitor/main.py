"""
Entry point for the Wi-Fi Monitor CLI.
Run with: python -m wifi_monitor.main <command> [options]
"""

import argparse
import sys
from wifi_monitor.ping_test import run_ping
from wifi_monitor.throughput_test import run_tcp_test, run_udp_test
from wifi_monitor.storage import init_db, save_result
from wifi_monitor.report import print_summary


def build_parser() -> argparse.ArgumentParser:
    """
    Build the argument parser with all subcommands.
    Each subcommand maps to one test type or action.
    """
    parser = argparse.ArgumentParser(
        prog="wifi-monitor",
        description="Wi-Fi Throughput and Latency Monitor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m wifi_monitor.main ping --host 8.8.8.8 --count 10
  python -m wifi_monitor.main throughput --server 192.168.1.10 --duration 10
  python -m wifi_monitor.main throughput --server 192.168.1.10 --protocol udp
  python -m wifi_monitor.main report --last 20
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.required = True

    ping_parser = subparsers.add_parser(
        "ping",
        help="Measure latency and packet loss using ping"
    )
    ping_parser.add_argument(
        "--host", required=True,
        help="Target hostname or IP (e.g. 8.8.8.8)"
    )
    ping_parser.add_argument(
        "--count", type=int, default=10,
        help="Number of ping packets to send (default: 10)"
    )

    tp_parser = subparsers.add_parser(
        "throughput",
        help="Measure bandwidth using iperf3 (requires iperf3 server)"
    )
    tp_parser.add_argument(
        "--server", required=True,
        help="IP or hostname of the iperf3 server"
    )
    tp_parser.add_argument(
        "--duration", type=int, default=10,
        help="Test duration in seconds (default: 10)"
    )
    tp_parser.add_argument(
        "--protocol", choices=["tcp", "udp"], default="tcp",
        help="Transport protocol: tcp (default) or udp"
    )
    tp_parser.add_argument(
        "--bandwidth", default="100M",
        help="UDP target bandwidth e.g. 100M, 1G (default: 100M, UDP only)"
    )
    tp_parser.add_argument(
        "--reverse", action="store_true",
        help="Reverse mode: measure download speed from server to client"
    )

    report_parser = subparsers.add_parser(
        "report",
        help="Show summary of recent test results"
    )
    report_parser.add_argument(
        "--last", type=int, default=10,
        help="Number of recent results to summarize (default: 10)"
    )
    report_parser.add_argument(
        "--type", choices=["ping", "throughput", "all"], default="all",
        help="Filter by test type (default: all)"
    )

    return parser


def handle_ping(args):
    """Run ping test, save result, print summary."""
    print(f"\n[ping] Testing latency to {args.host} ({args.count} packets)...")
    result = run_ping(host=args.host, count=args.count)
    save_result(result)

    if result["status"] == "SUCCESS":
        print(f"  Status       : {result['status']}")
        print(f"  Packets sent : {result['packets_sent']}")
        print(f"  Packet loss  : {result['packet_loss_pct']}%")
        print(f"  RTT avg      : {result['rtt_avg_ms']} ms")
        print(f"  RTT min/max  : {result['rtt_min_ms']} / {result['rtt_max_ms']} ms")
    else:
        print(f"  [FAILED] {result['error']}")
    print()


def handle_throughput(args):
    """Run TCP or UDP throughput test, save result, print summary."""
    mode = "download" if args.reverse else "upload"
    print(f"\n[throughput] Testing {args.protocol.upper()} {mode} to {args.server} "
          f"for {args.duration}s...")

    if args.protocol == "tcp":
        result = run_tcp_test(
            server=args.server,
            duration=args.duration,
            reverse=args.reverse
        )
    else:
        result = run_udp_test(
            server=args.server,
            duration=args.duration,
            bandwidth=args.bandwidth,
            reverse=args.reverse
        )

    save_result(result)

    if result["status"] == "SUCCESS":
        print(f"  Status       : {result['status']}")
        print(f"  Protocol     : {result['protocol']}")
        print(f"  Throughput   : {result['throughput_mbps']} Mbps")
        if result["jitter_ms"] is not None:
            print(f"  Jitter       : {result['jitter_ms']} ms")
        if result["packet_loss_pct"] is not None:
            print(f"  Packet loss  : {result['packet_loss_pct']}%")
    else:
        print(f"  [FAILED] {result['error']}")
    print()


def handle_report(args):
    """Show summary of recent test results from SQLite."""
    print_summary(last_n=args.last, test_type=args.type)


def main():
    init_db()  # create DB and table if not already there
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ping":
        handle_ping(args)
    elif args.command == "throughput":
        handle_throughput(args)
    elif args.command == "report":
        handle_report(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
