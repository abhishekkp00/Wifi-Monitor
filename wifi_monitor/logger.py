"""
logger.py
---------
Centralised logger for wifi-monitor.
Log level and log file path are read from config.
"""
from __future__ import annotations

import logging
import os

from wifi_monitor.config import get_cfg


_LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _build_logger() -> logging.Logger:
    log_level_str = get_cfg("logging", "level", "INFO")
    log_dir = get_cfg("logging", "log_dir", "data/logs")
    log_to_file = get_cfg("logging", "file", False)

    level = _LOG_LEVEL_MAP.get(str(log_level_str).upper(), logging.INFO)

    lgr = logging.getLogger("wifi_monitor")
    if lgr.handlers:
        return lgr

    lgr.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(module)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    lgr.addHandler(ch)

    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(os.path.join(log_dir, "wifi_monitor.log"))
        fh.setFormatter(fmt)
        lgr.addHandler(fh)

    return lgr


logger = _build_logger()


def setup_logging() -> logging.Logger:
    return logger