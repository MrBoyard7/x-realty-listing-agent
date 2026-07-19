"""Production client backed by the official X API v2.

This module intentionally requires the caller to already hold a valid
bearer token for an account that is authorized to read the target
(private) account's posts -- for example an approved/follower developer
account, or an X API plan that supports the required endpoint. This
project does not, and must not, accept or store the production
account's password; authentication is always via API credentials
configured through environment variables / Azure Function App settings.

See docs/SETUP.md for how to provision credentials for both the test
account (development) and the production account (deployment).
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import requests

from realty_agent.models import RawPost
from realty_agent.x_client.base import XClient

_API_BASE = "https://api.twitter.com/2"


class XApiClient(XClient):
    """Thin wrapper around the ``GET /2/users/:id/tweets`` endpoint."""

    def __init__(self, bearer_token: str, session: Optional[requests.Session] = None):
        if not bearer_token:
            raise ValueError("An X API bearer token is required to use XApiClient.")
        self._token = bearer_token
        self._session = session or requests.Session()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    def _user_id_for(self, username: str) -> str:
        resp = self._session.get(
            f"{_API_BASE}/users/by/username/{username}",
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["data"]["id"]

    def _list_tweets(self, user_id: str, params: dict) -> List[RawPost]:
        base_params = {
            "max_results": 100,
            "tweet.fields": "created_at,text",
        }
        base_params.update(params)
        resp = self._session.get(
            f"{_API_BASE}/users/{user_id}/tweets",
            headers=self._headers(),
            params=base_params,
            timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json()
        posts: List[RawPost] = []
        for item in payload.get("data", []):
            posts.append(
                RawPost(
                    post_id=item["id"],
                    text=item["text"],
                    created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
                    author_username=payload.get("includes", {}).get("username", ""),
                    url=f"https://x.com/i/web/status/{item['id']}",
                )
            )
        return posts

    def fetch_recent_posts(self, username: str, since_id: str | None = None) -> List[RawPost]:
        user_id = self._user_id_for(username)
        params = {}
        if since_id:
            params["since_id"] = since_id
        return self._list_tweets(user_id, params)

    def fetch_posts_since(self, username: str, since: datetime) -> List[RawPost]:
        user_id = self._user_id_for(username)
        params = {"start_time": since.isoformat()}
        return self._list_tweets(user_id, params)
