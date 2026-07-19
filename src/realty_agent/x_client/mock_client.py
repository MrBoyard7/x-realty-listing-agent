"""In-memory X client used for local development, demos, and tests.

This is what lets the whole pipeline be exercised end-to-end (parsing,
de-duplication, Excel writing, URL enrichment) without ever touching the
real X API or a private production account, per the project's
development/testing requirements.
"""

from __future__ import annotations

from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

from realty_agent.models import RawPost
from realty_agent.x_client.base import XClient

PHX = ZoneInfo("America/Phoenix")


class MockXClient(XClient):
    """A fixed or user-supplied list of posts, sorted newest first."""

    def __init__(self, posts: List[RawPost] | None = None):
        self._posts = sorted(posts or [], key=lambda p: p.created_at, reverse=True)

    def add_post(self, post: RawPost) -> None:
        self._posts.append(post)
        self._posts.sort(key=lambda p: p.created_at, reverse=True)

    def fetch_recent_posts(self, username: str, since_id: str | None = None) -> List[RawPost]:
        posts = [p for p in self._posts if p.author_username == username]
        if since_id is None:
            return posts
        try:
            since_index = next(i for i, p in enumerate(posts) if p.post_id == since_id)
        except StopIteration:
            return posts
        return posts[:since_index]

    def fetch_posts_since(self, username: str, since: datetime) -> List[RawPost]:
        return [p for p in self._posts if p.author_username == username and p.created_at >= since]

    @classmethod
    def with_sample_data(cls) -> "MockXClient":
        """Convenience constructor loading ``sample_data/sample_posts.json``.

        Sample post timestamps are expressed as ``days_ago`` + ``time``
        (relative to "now" in America/Phoenix) rather than fixed
        absolute dates, so the bundled demo and its accompanying delta
        sync / backfill behavior stay meaningful no matter when this
        repository is cloned and run.
        """
        import json
        from datetime import datetime, timedelta
        from pathlib import Path

        sample_path = Path(__file__).resolve().parents[3] / "sample_data" / "sample_posts.json"
        now = datetime.now(PHX)
        posts = []
        with open(sample_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        for item in data:
            day = (now - timedelta(days=item["days_ago"])).date()
            hour, minute, second = (int(part) for part in item["time"].split(":"))
            created_at = datetime(day.year, day.month, day.day, hour, minute, second, tzinfo=PHX)
            posts.append(
                RawPost(
                    post_id=item["post_id"],
                    text=item["text"],
                    created_at=created_at,
                    author_username=item["author_username"],
                    url=item["url"],
                )
            )
        return cls(posts)
