"""
Wi-Fi Throughput & Latency Monitor CLI
=======================================
A Linux-based tool to automate Wi-Fi network testing:
  - Latency & packet loss (ping)           [Day 2 ✅]
  - Throughput (iperf3)                    [Day 5]
  - Wi-Fi metadata (nmcli)                 [Day 7]
  - Persistent result storage (SQLite)     [Day 6]
  - Summary reports                        [Day 8]
"""

import argparse
import sys

from wifi_monitor import ping_test
from wifi_monitor.utils import require_command


# ─────────────────────────────────────────────
# Subcommand handlers
# ─────────────────────────────────────────────

def handle_ping(args):
    """Run ping test and display results."""
    require_command("ping", "sudo apt install iputils-ping")

    print(f"\nRunning ping test → host: {args.host}  count: {args.count}\n")

    result = ping_test.run_ping(host=args.host, count=args.count)
    print(ping_test.format_result(result))


def handle_throughput(args):
    """Run iperf3 throughput test."""
    print(f"[throughput] server: {args.server}  duration: {args.duration}s  protocol: {args.protocol}")
    print("[throughput] Module not implemented yet — coming in Day 5.")


def handle_wifi_info(args):
    """Fetch current Wi-Fi connection metadata."""
    print("[wifi-info] Fetching Wi-Fi metadata via nmcli...")
    print("[wifi-info] Module not implemented yet — coming in Day 7.")


def handle_run_suite(args):
    """Run all tests together."""
    print(f"[run-suite] host: {args.host}  server: {args.server}")
    print("[run-suite] Module not implemented yet — coming in Day 8.")


def handle_report(args):
    """Show summary of stored results."""
    print(f"[report] Showing last {args.last} results...")
    print("[report] Module not implemented yet — coming in Day 8.")


def handle_export(args):
    """Export results to CSV or JSON."""
    print(f"[export] Format: {args.format}")
    print("[export] Module not implemented yet — coming in Day 8.")


# ─────────────────────────────────────────────
# CLI Parser
# ─────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="wifi-monitor",
        description=(
            "Wi-Fi Throughput & Latency Monitor CLI\n"
            "--------------------------------------\n"
            "Automates Wi-Fi network testing using ping, iperf3, nmcli.\n"
            "Results are stored in SQLite and summarized on demand."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m wifi_monitor.main ping --host 8.8.8.8 --count 10\n"
            "  python -m wifi_monitor.main throughput --server 192.168.1.10 --duration 10\n"
            "  python -m wifi_monitor.main wifi-info\n"
            "  python -m wifi_monitor.main run-suite --host 8.8.8.8 --server 192.168.1.10\n"
            "  python -m wifi_monitor.main report --last 20\n"
            "  python -m wifi_monitor.main export --format csv\n"
        ),
    )

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    subparsers = parser.add_subparsers(
        title="Available Commands",
        dest="command",
        metavar="<command>",
    )

    # ping
    ping_p = subparsers.add_parser("ping",
        help="Measure latency and packet loss to a target host.",
        description="Runs ping and parses RTT (min/avg/max) and packet loss %.")
    ping_p.add_argument("--host", type=str, default="8.8.8.8",
        help="Target host/IP to ping. Default: 8.8.8.8")
    ping_p.add_argument("--count", type=int, default=10,
        help="Number of ping packets to send. Default: 10")
    ping_p.set_defaults(func=handle_ping)

    # throughput
    tp_p = subparsers.add_parser("throughput",
        help="Measure network throughput using iperf3.",
        description="Connects to an iperf3 server and measures TCP/UDP bandwidth.")
    tp_p.add_argument("--server", type=str, required=True,
        help="IP address of the iperf3 server.")
    tp_p.add_argument("--duration", type=int, default=10,
        help="Test duration in seconds. Default: 10")
    tp_p.add_argument("--protocol", type=str, choices=["tcp", "udp"], default="tcp",
        help="Protocol to use. Default: tcp")
    tp_p.set_defaults(func=handle_throughput)

    # wifi-info
    wifi_p = subparsers.add_parser("wifi-info",
        help="Show current Wi-Fi connection details (SSID, interface, IP).",
        description="Uses nmcli to fetch active Wi-Fi connection metadata.")
    wifi_p.set_defaults(func=handle_wifi_info)

    # run-suite
    suite_p = subparsers.add_parser("run-suite",
        help="Run all tests (ping + throughput + wifi-info) in one go.",
        description="Runs a full test suite and stores all results in SQLite.")
    suite_p.add_argument("--host", type=str, default="8.8.8.8",
        help="Target host for ping. Default: 8.8.8.8")
    suite_p.add_argument("--server", type=str, required=True,
        help="iperf3 server IP.")
    suite_p.add_argument("--count", type=int, default=10,
        help="Ping count. Default: 10")
    suite_p.add_argument("--duration", type=int, default=10,
        help="iperf3 duration in seconds. Default: 10")
    suite_p.set_defaults(func=handle_run_suite)

    # report
    report_p = subparsers.add_parser("report",
        help="Show summary of stored test results.",
        description="Reads SQLite and prints avg RTT, loss, throughput stats.")
    report_p.add_argument("--last", type=int, default=10,
        help="Show last N results. Default: 10")
    report_p.set_defaults(func=handle_report)

    # export
    export_p = subparsers.add_parser("export",
        help="Export stored results to CSV or JSON.",
        description="Reads SQLite and exports all results.")
    export_p.add_argument("--format", type=str, choices=["csv", "json"], default="csv",
        help="Export format. Default: csv")
    export_p.set_defaults(func=handle_export)

    return parser


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()