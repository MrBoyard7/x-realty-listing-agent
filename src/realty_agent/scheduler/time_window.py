"""Decide whether "now" falls inside the configured operating window.

The Azure Function itself is triggered on a fixed timer (every 5
minutes, see ``azure_function/function_app.py``), but the *days* and
*hours* during which it should actually do work are configurable data,
not code -- this module is the single place that interprets them.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Iterable

_DAY_NAME_TO_WEEKDAY = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def is_within_operating_window(
    now: datetime,
    operating_days: Iterable[str],
    operating_start: str,
    operating_end: str,
) -> bool:
    """``now`` must already be timezone-aware in the target timezone."""
    allowed_weekdays = {_DAY_NAME_TO_WEEKDAY[d.strip().lower()[:3]] for d in operating_days}
    if now.weekday() not in allowed_weekdays:
        return False

    start = _parse_hhmm(operating_start)
    end = _parse_hhmm(operating_end)
    return start <= now.time() <= end
