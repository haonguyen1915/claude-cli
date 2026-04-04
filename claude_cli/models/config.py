"""Configuration schema models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AccountConfig(BaseModel):
    """Single account configuration."""

    label: str
    tier: Literal["pro", "max", "team", "enterprise"]
    created_at: datetime


class Config(BaseModel):
    """Root configuration schema."""

    accounts: dict[str, AccountConfig] = Field(default_factory=dict)
    default: str | None = None
