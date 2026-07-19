"""Persisted "high water mark" for delta sync.

Tracks the most recently processed X post id and its date/time so that
each run only asks X for posts newer than that, per the spec's delta
sync requirement. Stored as a small JSON file that lives next to the
workbook (and therefore gets backed up/synced the same way).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SyncState:
    last_post_id: Optional[str] = None
    last_post_date_time: Optional[str] = None  # ISO 8601

    @classmethod
    def load(cls, path: Path) -> "SyncState":
        if not path.exists():
            return cls()
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(**data)

    def save(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, indent=2)

    def update(self, post_id: str, post_date_time: datetime) -> None:
        self.last_post_id = post_id
        self.last_post_date_time = post_date_time.isoformat()
