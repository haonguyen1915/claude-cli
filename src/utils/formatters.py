"""Date and display formatting helpers."""

from __future__ import annotations

from datetime import date, datetime, timezone


def format_date(dt: datetime | date) -> str:
    """Format a datetime or date to YYYY-MM-DD."""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    return dt.isoformat()


def format_date_range(start: date, end: date) -> str:
    """Format a date range as 'Mon DD — Mon DD'."""
    return f"{start.strftime('%b %d')} \u2014 {end.strftime('%b %d')}"
