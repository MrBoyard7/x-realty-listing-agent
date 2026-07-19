"""Lightweight fakes for ``requests.Session`` used to unit-test the
network-facing clients (``XApiClient``, ``OneDriveClient``) without ever
making a real HTTP call.
"""

from __future__ import annotations

from typing import Any, List

import requests


class FakeResponse:
    def __init__(self, json_data: Any = None, status_code: int = 200, content: bytes = b""):
        self._json_data = json_data
        self.status_code = status_code
        self.content = content

    def json(self) -> Any:
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    """Returns queued responses in call order, regardless of HTTP verb."""

    def __init__(self, responses: List[FakeResponse]):
        self._responses = list(responses)
        self.calls: List[dict] = []

    def _pop(self) -> FakeResponse:
        if not self._responses:
            raise AssertionError("FakeSession ran out of queued responses")
        return self._responses.pop(0)

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append({"method": "GET", "url": url, "headers": headers, "params": params})
        return self._pop()

    def post(self, url, data=None, timeout=None):
        self.calls.append({"method": "POST", "url": url, "data": data})
        return self._pop()

    def put(self, url, headers=None, data=None, timeout=None):
        self.calls.append({"method": "PUT", "url": url, "headers": headers, "data": data})
        return self._pop()
