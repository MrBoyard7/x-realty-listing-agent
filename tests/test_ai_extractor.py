import json
from datetime import datetime
from zoneinfo import ZoneInfo

from realty_agent.extraction.ai_extractor import extract_with_ai
from realty_agent.models import RawPost

PHX = ZoneInfo("America/Phoenix")


def make_post(text: str) -> RawPost:
    return RawPost(
        post_id="1",
        text=text,
        created_at=datetime(2026, 6, 1, 9, 0, tzinfo=PHX),
        author_username="test_wholesale_deals",
        url="https://x.com/test_wholesale_deals/status/1",
    )


def test_no_completion_function_returns_blank_listing():
    post = make_post("some unstructured text")
    listing = extract_with_ai(post, complete=None)
    assert listing.address is None
    assert listing.notes == post.text


def test_completion_function_populates_fields():
    def fake_complete(prompt: str) -> str:
        return json.dumps(
            {
                "address": "123 Main St",
                "city": "Tempe",
                "state": "AZ",
                "zip_code": "85281",
                "beds": 3,
                "baths": 2,
                "square_feet": 1200,
                "price": 250000,
                "arv": 300000,
                "age_of_roof": None,
                "age_of_ac": None,
            }
        )

    post = make_post("3 bed 2 bath house in tempe, $250k")
    listing = extract_with_ai(post, complete=fake_complete)
    assert listing.address == "123 Main St"
    assert listing.beds == 3
    assert listing.price == 250000


def test_malformed_ai_response_degrades_gracefully():
    def fake_complete(prompt: str) -> str:
        return "not json at all"

    post = make_post("some text")
    listing = extract_with_ai(post, complete=fake_complete)
    assert listing.address is None
