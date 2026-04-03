"""Usage data models."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class UsagePeriod(BaseModel):
    """Billing period range."""

    start: date
    end: date


class RateWindow(BaseModel):
    """A single rate limit window (e.g. 5-hour session, 7-day weekly)."""

    utilization: float  # 0-100 percentage
    resets_at: datetime


class ExtraUsage(BaseModel):
    """Extra/overage usage info."""

    is_enabled: bool = False
    monthly_limit: float | None = None
    used_credits: float | None = None
    utilization: float | None = None


class ApiUsageData(BaseModel):
    """Raw usage data from the Anthropic OAuth usage API."""

    five_hour: RateWindow | None = None
    seven_day: RateWindow | None = None
    seven_day_opus: RateWindow | None = None
    seven_day_sonnet: RateWindow | None = None
    extra_usage: ExtraUsage | None = None


class UsageInfo(BaseModel):
    """Usage information for a single account."""

    account_name: str
    tier: str
    period: UsagePeriod | None = None
    status: str = "Unknown"
    label: str = ""
    api_usage: ApiUsageData | None = None
