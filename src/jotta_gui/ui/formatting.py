from __future__ import annotations

from datetime import datetime


def format_bytes(value: int | None) -> str:
    """Format a byte count using decimal units.

    ``None`` is deliberately rendered as unknown instead of as zero because the
    CLI contract distinguishes a missing fact from a reported value of 0.
    """

    if value is None:
        return "—"

    units = ("B", "KB", "MB", "GB", "TB", "PB", "EB")
    size = float(value)

    for unit in units:
        if abs(size) < 1000 or unit == units[-1]:
            precision = 0 if unit == "B" else 1
            return f"{size:.{precision}f} {unit}"
        size /= 1000

    return f"{size:.1f} EB"


def format_count(value: int | None) -> str:
    return "—" if value is None else f"{value:,}"


def format_percent(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}%"


def percentage(value: int | None, total: int | None) -> float | None:
    if value is None or total is None or total <= 0:
        return None
    return min(max(value / total * 100, 0.0), 100.0)


def format_timestamp_ms(value: int | None) -> str:
    if value is None:
        return "Unknown"
    try:
        return datetime.fromtimestamp(value / 1000).astimezone().strftime("%Y-%m-%d %H:%M")
    except (OSError, OverflowError, ValueError):
        return "Unknown"
