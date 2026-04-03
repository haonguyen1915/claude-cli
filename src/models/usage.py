"""Usage data models."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class UsagePeriod(BaseModel):
    """Billing period range."""

    start: date
    end: date


class UsageInfo(BaseModel):
    """Usage information for a single account."""

    account_name: str
    tier: str
    period: UsagePeriod | None = None
    status: str = "Unknown"
    label: str = ""
