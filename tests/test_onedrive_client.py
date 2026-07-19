from pathlib import Path

import pytest

from fakes import FakeResponse, FakeSession
from realty_agent.storage.onedrive_client import OneDriveClient


def make_client(session: FakeSession) -> OneDriveClient:
    return OneDriveClient(
        tenant_id="tenant-1",
        client_id="client-1",
        client_secret="secret-1",
        drive_id="drive-1",
        session=session,
    )


def test_authenticate_posts_client_credentials_and_caches_token():
    session = FakeSession(
        [
            FakeResponse({"access_token": "tok-abc"}),  # token request
            FakeResponse(content=b"workbook-bytes"),  # download
            FakeResponse(content=b"workbook-bytes"),  # download again
        ]
    )
    client = make_client(session)

    token1 = client._authenticate()
    token2 = client._authenticate()

    assert token1 == "tok-abc"
    assert token2 == "tok-abc"
    # Only one POST to the token endpoint despite two _authenticate() calls.
    assert sum(1 for c in session.calls if c["method"] == "POST") == 1
    token_call = next(c for c in session.calls if c["method"] == "POST")
    assert "tenant-1/oauth2/v2.0/token" in token_call["url"]
    assert token_call["data"]["client_id"] == "client-1"
    assert token_call["data"]["client_secret"] == "secret-1"
    assert token_call["data"]["grant_type"] == "client_credentials"


def test_download_writes_bytes_to_local_path(tmp_path: Path):
    session = FakeSession(
        [
            FakeResponse({"access_token": "tok-abc"}),
            FakeResponse(content=b"the workbook bytes"),
        ]
    )
    client = make_client(session)
    local_path = tmp_path / "listings.xlsx"

    client.download("/RealEstate/listings.xlsx", local_path)

    assert local_path.read_bytes() == b"the workbook bytes"
    get_call = next(c for c in session.calls if c["method"] == "GET")
    assert "drives/drive-1/root:/RealEstate/listings.xlsx:/content" in get_call["url"]
    assert get_call["headers"]["Authorization"] == "Bearer tok-abc"


def test_upload_sends_correct_url_and_content_type(tmp_path: Path):
    session = FakeSession(
        [
            FakeResponse({"access_token": "tok-abc"}),
            FakeResponse(status_code=200),
        ]
    )
    client = make_client(session)
    local_path = tmp_path / "listings.xlsx"
    local_path.write_bytes(b"data")

    client.upload("/RealEstate/listings.xlsx", local_path)

    put_call = next(c for c in session.calls if c["method"] == "PUT")
    assert "drives/drive-1/root:/RealEstate/listings.xlsx:/content" in put_call["url"]
    assert put_call["headers"]["Authorization"] == "Bearer tok-abc"
    assert (
        put_call["headers"]["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_download_http_error_propagates(tmp_path: Path):
    session = FakeSession(
        [
            FakeResponse({"access_token": "tok-abc"}),
            FakeResponse(status_code=403),
        ]
    )
    client = make_client(session)
    with pytest.raises(Exception):
        client.download("/RealEstate/listings.xlsx", tmp_path / "out.xlsx")
