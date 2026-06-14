"""
cli.py
------
CLI argument parser for wifi-monitor.
"""
from __future__ import annotations
import argparse
from wifi_monitor.config import get_cfg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wi-Fi/network quality monitor CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to run")

    # ping
    ping_parser = subparsers.add_parser("ping", help="Run a ping (ICMP) test")
    ping_parser.add_argument("--host", default=get_cfg("ping", "default_host", "8.8.8.8"), help="Host to ping")
    ping_parser.add_argument("--count", type=int, default=get_cfg("ping", "default_count", 10), help="Number of packets to send")
    ping_parser.add_argument("--interval", type=float, default=get_cfg("ping", "default_interval", 1.0), help="Seconds between packets")
    ping_parser.add_argument("--no-save", action="store_true", help="Do not save results to database")

    # throughput
    tp_parser = subparsers.add_parser("throughput", help="Run a throughput test using iperf3")
    tp_parser.add_argument("--server", default=get_cfg("throughput", "default_server", "127.0.0.1"), help="iperf3 server address")
    tp_parser.add_argument("--duration", type=int, default=get_cfg("throughput", "default_duration", 10), help="Duration in seconds")
    tp_parser.add_argument("--protocol", choices=["tcp", "udp"], default=get_cfg("throughput", "default_protocol", "tcp"), help="Protocol to use")
    tp_parser.add_argument("--bandwidth", help="Bandwidth limit for UDP (e.g. 10M, 1G)")
    tp_parser.add_argument("--port", type=int, default=get_cfg("throughput", "default_port", 5201), help="Port of the iperf3 server")
    tp_parser.add_argument("--no-save", action="store_true", help="Do not save results to database")

    # wifi-info
    subparsers.add_parser("wifi-info", help="Show current Wi-Fi connection info")

    # run-suite
    suite_parser = subparsers.add_parser("run-suite", help="Run both ping and throughput tests")
    suite_parser.add_argument("--host", default=get_cfg("ping", "default_host", "8.8.8.8"), help="Host to ping")
    suite_parser.add_argument("--count", type=int, default=get_cfg("ping", "default_count", 10), help="Number of packets to send")
    suite_parser.add_argument("--interval", type=float, default=get_cfg("ping", "default_interval", 1.0), help="Seconds between packets")
    suite_parser.add_argument("--server", default=get_cfg("throughput", "default_server", "127.0.0.1"), help="iperf3 server address")
    suite_parser.add_argument("--duration", type=int, default=get_cfg("throughput", "default_duration", 10), help="Duration in seconds")
    suite_parser.add_argument("--protocol", choices=["tcp", "udp"], default=get_cfg("throughput", "default_protocol", "tcp"), help="Protocol to use")
    suite_parser.add_argument("--bandwidth", help="Bandwidth limit for UDP (e.g. 10M, 1G)")
    suite_parser.add_argument("--port", type=int, default=get_cfg("throughput", "default_port", 5201), help="Port of the iperf3 server")
    suite_parser.add_argument("--no-save", action="store_true", help="Do not save results to database")

    # report
    report_parser = subparsers.add_parser("report", help="Show a summary report of past test runs")
    report_parser.add_argument("--last", type=int, default=get_cfg("report", "default_last", 20), help="Number of runs to aggregate")
    report_parser.add_argument("--test-type", choices=["ping", "throughput", "all"], default="all", help="Filter by test type")

    # export
    export_parser = subparsers.add_parser("export", help="Export test results to a file")
    export_parser.add_argument("--last", type=int, default=get_cfg("export", "default_limit", 100), help="Number of recent runs to export")
    export_parser.add_argument("--format", choices=["csv", "json"], default=get_cfg("export", "default_format", "csv"), help="Format of the export file")
    export_parser.add_argument("--output", help="Path to output file")

    # schedule
    schedule_parser = subparsers.add_parser("schedule", help="Start the periodic scheduler")
    schedule_parser.add_argument("--interval", type=int, default=get_cfg("scheduler", "interval_seconds", 60), help="Interval between runs in seconds")

    # dashboard
    db_parser = subparsers.add_parser("dashboard", help="Start the web dashboard")
    db_parser.add_argument("--host", default=get_cfg("dashboard", "host", "127.0.0.1"), help="Host to bind to")
    db_parser.add_argument("--port", type=int, default=get_cfg("dashboard", "port", 5000), help="Port to bind to")
    db_parser.add_argument("--debug", action="store_true", default=get_cfg("dashboard", "debug", True), help="Run in Flask debug mode")

    return parser