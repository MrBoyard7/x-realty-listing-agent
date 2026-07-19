from datetime import datetime, timezone

import pytest

from fakes import FakeResponse, FakeSession
from realty_agent.x_client.x_api_client import XApiClient


def test_missing_bearer_token_raises_value_error():
    with pytest.raises(ValueError):
        XApiClient(bearer_token="")


def test_user_id_lookup_and_recent_posts():
    session = FakeSession(
        [
            FakeResponse({"data": {"id": "42"}}),  # GET users/by/username/...
            FakeResponse(  # GET users/42/tweets
                {
                    "data": [
                        {
                            "id": "999",
                            "text": "4/2 1678 ft2",
                            "created_at": "2026-06-01T12:00:00Z",
                        }
                    ],
                    "includes": {"username": "test_wholesale_deals"},
                }
            ),
        ]
    )
    client = XApiClient(bearer_token="tok", session=session)
    posts = client.fetch_recent_posts("test_wholesale_deals")

    assert len(posts) == 1
    assert posts[0].post_id == "999"
    assert posts[0].text == "4/2 1678 ft2"
    assert posts[0].created_at == datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    assert posts[0].url == "https://x.com/i/web/status/999"

    # First call resolves the username, second call lists tweets.
    assert session.calls[0]["method"] == "GET"
    assert "users/by/username/test_wholesale_deals" in session.calls[0]["url"]
    assert session.calls[1]["url"].endswith("/users/42/tweets")
    assert "Authorization" in session.calls[0]["headers"]
    assert session.calls[0]["headers"]["Authorization"] == "Bearer tok"


def test_fetch_recent_posts_includes_since_id_param():
    session = FakeSession(
        [
            FakeResponse({"data": {"id": "42"}}),
            FakeResponse({"data": []}),
        ]
    )
    client = XApiClient(bearer_token="tok", session=session)
    client.fetch_recent_posts("test_wholesale_deals", since_id="123")

    tweets_call = session.calls[1]
    assert tweets_call["params"]["since_id"] == "123"


def test_fetch_recent_posts_without_since_id_omits_param():
    session = FakeSession(
        [
            FakeResponse({"data": {"id": "42"}}),
            FakeResponse({"data": []}),
        ]
    )
    client = XApiClient(bearer_token="tok", session=session)
    client.fetch_recent_posts("test_wholesale_deals")

    tweets_call = session.calls[1]
    assert "since_id" not in tweets_call["params"]


def test_fetch_posts_since_includes_start_time_param():
    session = FakeSession(
        [
            FakeResponse({"data": {"id": "42"}}),
            FakeResponse({"data": []}),
        ]
    )
    client = XApiClient(bearer_token="tok", session=session)
    since = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
    client.fetch_posts_since("test_wholesale_deals", since)

    tweets_call = session.calls[1]
    assert tweets_call["params"]["start_time"] == since.isoformat()


def test_http_error_propagates():
    session = FakeSession([FakeResponse(status_code=404)])
    client = XApiClient(bearer_token="tok", session=session)
    with pytest.raises(Exception):
        client.fetch_recent_posts("nonexistent_user")


def test_empty_tweets_response_returns_empty_list():
    session = FakeSession(
        [
            FakeResponse({"data": {"id": "42"}}),
            FakeResponse({"data": []}),
        ]
    )
    client = XApiClient(bearer_token="tok", session=session)
    assert client.fetch_recent_posts("test_wholesale_deals") == []
