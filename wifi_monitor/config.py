"""
config.py
---------
Single source of truth for all runtime configuration.

Load order (highest priority first):
  1. path passed directly to load_config(path=...)
  2. WIFI_MONITOR_CONFIG environment variable
  3. config/default.json  (relative to this file)
  4. _FALLBACKS dict      (last resort — file missing)
"""

from __future__ import annotations
import json
import os

_DEFAULT_CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "config", "default.json")
)

# Mirror of default.json — only used if the file is missing entirely.
_FALLBACKS: dict = {
    "ping":       {"default_host": "8.8.8.8", "default_count": 10, "default_interval": 1.0},
    "throughput": {"default_server": "192.168.1.10", "default_duration": 10,
                   "default_protocol": "tcp", "default_port": 5201},
    "thresholds": {"loss_warn_pct": 2.0, "throughput_warn_mbps": 10.0},
    "export":     {"default_limit": 100, "default_format": "csv"},
    "report":     {"default_last": 20},
}

_cache: dict | None = None


def load_config(path: str | None = None, force_reload: bool = False) -> dict:
    """
    Load and return the full config dict.
    Results are cached in memory — subsequent calls are free.
    Pass force_reload=True in tests to reset between test cases.
    """
    global _cache
    if _cache is not None and not force_reload and path is None:
        return _cache

    target = path or os.environ.get("WIFI_MONITOR_CONFIG", _DEFAULT_CONFIG_PATH)

    try:
        with open(target, encoding="utf-8") as fh:
            cfg = json.load(fh)
        _cache = cfg
        return cfg
    except FileNotFoundError:
        _cache = _FALLBACKS
        return _FALLBACKS
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in config file '{target}': {exc}") from exc


def get_cfg(section: str, key: str, fallback=None):
    """
    Convenience one-liner accessor.

    Usage:
        count = get_cfg("ping", "default_count")
        port  = get_cfg("throughput", "default_port")
    """
    return load_config().get(section, {}).get(key, fallback)