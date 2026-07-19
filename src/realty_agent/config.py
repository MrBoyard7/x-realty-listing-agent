"""Runtime configuration loading.

All values that the project spec requires to be configurable *without
modifying source code* live here and are read from a YAML file (see
``config/settings.example.yaml``) with environment-variable overrides for
anything secret (API keys, tenant IDs, etc.).

Environment variables always take precedence over the YAML file so that
the same config file can be safely committed to source control while
secrets stay in Azure Function App settings / local ``.env`` files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "settings.yaml"


@dataclass
class Settings:
    # --- X account ---
    x_username: str
    x_bearer_token: Optional[str]

    # --- OneDrive / Excel ---
    onedrive_drive_id: Optional[str]
    onedrive_file_path: str  # e.g. "/RealEstate/listings.xlsx"

    # --- Schedule ---
    timezone: str
    operating_days: list  # e.g. ["Mon", "Tue", "Wed", "Thu", "Fri"]
    operating_start: str  # "06:00"
    operating_end: str  # "18:00"
    sync_frequency_minutes: int

    # --- Backfill ---
    backfill_days: int

    # --- AI model ---
    ai_provider: str  # "anthropic" | "openai" | "none"
    ai_model: str

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Settings":
        path = path or DEFAULT_CONFIG_PATH
        raw: dict = {}
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}

        def get(key: str, default: Any = None) -> Any:
            env_key = "REALTY_AGENT_" + key.upper()
            if env_key in os.environ:
                return os.environ[env_key]
            return raw.get(key, default)

        return cls(
            x_username=get("x_username", ""),
            x_bearer_token=get("x_bearer_token"),
            onedrive_drive_id=get("onedrive_drive_id"),
            onedrive_file_path=get("onedrive_file_path", "/RealEstate/listings.xlsx"),
            timezone=get("timezone", "America/Phoenix"),
            operating_days=get("operating_days", ["Mon", "Tue", "Wed", "Thu", "Fri"]),
            operating_start=get("operating_start", "06:00"),
            operating_end=get("operating_end", "18:00"),
            sync_frequency_minutes=int(get("sync_frequency_minutes", 5)),
            backfill_days=int(get("backfill_days", 0)),
            ai_provider=get("ai_provider", "none"),
            ai_model=get("ai_model", "claude-haiku-4-5-20251001"),
        )
