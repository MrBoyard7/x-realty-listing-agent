"""Abstract interface for reading posts from X.

Keeping this as a small protocol means the rest of the pipeline never
needs to know whether it is talking to the real X API, an internal
proxy/MCP server, or a local mock used in tests and demos.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from realty_agent.models import RawPost


class XClient(ABC):
    """Read-only client capable of listing posts for one username."""

    @abstractmethod
    def fetch_recent_posts(self, username: str, since_id: str | None = None) -> List[RawPost]:
        """Return posts newer than ``since_id`` (delta sync), newest first."""

    @abstractmethod
    def fetch_posts_since(self, username: str, since: datetime) -> List[RawPost]:
        """Return posts created at or after ``since`` (used for backfill)."""
