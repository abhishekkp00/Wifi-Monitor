from __future__ import annotations

from datetime import datetime, timezone
from shutil import which
from typing import Any


EMPTY_STRINGS = {"", "na", "n/a", "none", "null", "nil", "unknown", "-"}


def format_timestamp() -> str:
    """
    Return current UTC time as ISO 8601 string.
    Example: 2026-06-13T08:30:00.123456+00:00
    """
    return datetime.now(timezone.utc).isoformat()


def is_tool_installed(tool_name: str) -> bool:
    """
    Return True if a command-line tool is available in PATH.
    Example: is_tool_installed("ping") -> True
    """
    return which(tool_name) is not None


def clean_text(value: Any) -> str | None:
    """
    Normalize text values coming from CLI output, config, or DB.
    Returns None for empty or placeholder values.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.lower() in EMPTY_STRINGS:
        return None
    return text


def safe_int(value: Any) -> int | None:
    """
    Convert value to int when possible, else return None.
    Handles strings like '10', '10.0', and whitespace safely.
    """
    value = clean_text(value)
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def safe_float(value: Any, digits: int | None = None) -> float | None:
    """
    Convert value to float when possible, else return None.
    Optional rounding can be applied using digits.
    """
    value = clean_text(value)
    if value is None:
        return None
    try:
        num = float(value)
        return round(num, digits) if digits is not None else num
    except (TypeError, ValueError):
        return None


def to_bool(value: Any) -> bool:
    """
    Convert common truthy/falsy values into bool.
    Useful for config flags.
    """
    if isinstance(value, bool):
        return value
    value = clean_text(value)
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "y", "on"}


def merge_dicts(base: dict | None, extra: dict | None) -> dict:
    """
    Merge two dicts safely without mutating inputs.
    None inputs are treated as empty dicts.
    """
    merged = {}
    if base:
        merged.update(base)
    if extra:
        merged.update(extra)
    return merged


def compact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """
    Return a copy of a dict with keys containing None values removed.
    """
    return {k: v for k, v in data.items() if v is not None}


def ensure_keys(data: dict[str, Any], keys: list[str], default: Any = None) -> dict[str, Any]:
    """
    Ensure a dict contains a required set of keys.
    Missing keys are added with the provided default.
    """
    out = dict(data)
    for key in keys:
        out.setdefault(key, default)
    return out
