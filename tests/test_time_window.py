from datetime import datetime
from zoneinfo import ZoneInfo

from realty_agent.scheduler.time_window import is_within_operating_window

PHX = ZoneInfo("America/Phoenix")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]


def test_weekday_within_hours_is_open():
    now = datetime(2026, 6, 1, 9, 0, tzinfo=PHX)  # Monday
    assert is_within_operating_window(now, DAYS, "06:00", "18:00") is True


def test_weekday_before_hours_is_closed():
    now = datetime(2026, 6, 1, 5, 59, tzinfo=PHX)
    assert is_within_operating_window(now, DAYS, "06:00", "18:00") is False


def test_weekday_after_hours_is_closed():
    now = datetime(2026, 6, 1, 18, 1, tzinfo=PHX)
    assert is_within_operating_window(now, DAYS, "06:00", "18:00") is False


def test_saturday_is_closed():
    now = datetime(2026, 6, 6, 9, 0, tzinfo=PHX)  # Saturday
    assert is_within_operating_window(now, DAYS, "06:00", "18:00") is False


def test_sunday_is_closed():
    now = datetime(2026, 6, 7, 9, 0, tzinfo=PHX)  # Sunday
    assert is_within_operating_window(now, DAYS, "06:00", "18:00") is False


def test_boundary_start_and_end_are_inclusive():
    start = datetime(2026, 6, 1, 6, 0, tzinfo=PHX)
    end = datetime(2026, 6, 1, 18, 0, tzinfo=PHX)
    assert is_within_operating_window(start, DAYS, "06:00", "18:00") is True
    assert is_within_operating_window(end, DAYS, "06:00", "18:00") is True
