"""Minimal Microsoft Graph wrapper for downloading/uploading the workbook.

Uses application permissions (client-credentials flow) against a single
OneDrive/SharePoint file path, which is the simplest supported
authentication model for an unattended Azure Function -- no user needs
to be signed in at run time.

Required Azure AD app registration permissions: ``Files.ReadWrite.All``
(application). See docs/SETUP.md for the full app-registration walkthrough.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import requests

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_LOGIN_BASE = "https://login.microsoftonline.com"


class OneDriveClient:
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        drive_id: str,
        session: Optional[requests.Session] = None,
    ):
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._drive_id = drive_id
        self._session = session or requests.Session()
        self._access_token: Optional[str] = None

    def _authenticate(self) -> str:
        if self._access_token:
            return self._access_token
        resp = self._session.post(
            f"{_LOGIN_BASE}/{self._tenant_id}/oauth2/v2.0/token",
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            },
            timeout=15,
        )
        resp.raise_for_status()
        self._access_token = resp.json()["access_token"]
        return self._access_token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._authenticate()}"}

    def download(self, item_path: str, local_path: Path) -> None:
        url = f"{_GRAPH_BASE}/drives/{self._drive_id}/root:{item_path}:/content"
        resp = self._session.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        local_path.write_bytes(resp.content)

    def upload(self, item_path: str, local_path: Path) -> None:
        url = f"{_GRAPH_BASE}/drives/{self._drive_id}/root:{item_path}:/content"
        with open(local_path, "rb") as fh:
            resp = self._session.put(
                url,
                headers={
                    **self._headers(),
                    "Content-Type": (
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ),
                },
                data=fh,
                timeout=60,
            )
        resp.raise_for_status()
