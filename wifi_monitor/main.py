"""main.py — Entry point. Routes commands. No business logic."""
from __future__ import annotations
import sys
from wifi_monitor.logger   import setup_logging
from wifi_monitor.cli      import build_parser
from wifi_monitor.commands import (
    cmd_ping, cmd_throughput, cmd_wifi_info, cmd_run_suite,
    cmd_report, cmd_export, cmd_schedule, cmd_dashboard,
)

_DISPATCH = {
    "ping":        cmd_ping,
    "throughput":  cmd_throughput,
    "wifi-info":   cmd_wifi_info,
    "run-suite":   cmd_run_suite,
    "report":      cmd_report,
    "export":      cmd_export,
    "schedule":    cmd_schedule,
    "dashboard":   cmd_dashboard,
}


def main() -> int:
    setup_logging()
    parser  = build_parser()
    args    = parser.parse_args()
    handler = _DISPATCH.get(args.command)
    if not handler:
        parser.print_help(); return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())