"""
scheduler.py
------------
Periodic auto-runner. Interval and targets from config.
"""
from __future__ import annotations
import time
import threading
from wifi_monitor.config      import get_cfg
from wifi_monitor.ping_test   import run_ping
from wifi_monitor.throughput_test import run_throughput
from wifi_monitor.storage     import save_result
from wifi_monitor.logger      import logger

_stop_event = threading.Event()


def run_once() -> dict:
    host    = get_cfg("scheduler", "ping_host",    "8.8.8.8")
    server  = get_cfg("scheduler", "iperf_server", "127.0.0.1")
    run_tp  = get_cfg("scheduler", "run_throughput", False)

    results = {}

    logger.info("[scheduler] running ping → %s", host)
    ping_result = run_ping(host=host)
    save_result(ping_result)
    results["ping"] = ping_result

    if run_tp:
        logger.info("[scheduler] running throughput → %s", server)
        tp_result = run_throughput(server=server)
        save_result(tp_result)
        results["throughput"] = tp_result

    return results


def start_scheduler(interval: int | None = None) -> threading.Thread:
    interval = interval or get_cfg("scheduler", "interval_seconds", 60)

    def _loop():
        logger.info("[scheduler] started — interval=%ds", interval)
        while not _stop_event.is_set():
            try:
                run_once()
            except Exception as exc:
                logger.error("[scheduler] error: %s", exc)
            _stop_event.wait(timeout=interval)
        logger.info("[scheduler] stopped")

    t = threading.Thread(target=_loop, name="wifi-scheduler", daemon=True)
    t.start()
    return t


def stop_scheduler():
    _stop_event.set()