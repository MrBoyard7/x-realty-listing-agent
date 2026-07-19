from datetime import datetime
from zoneinfo import ZoneInfo

from realty_agent.extraction.parser import needs_ai_fallback, parse_post
from realty_agent.models import RawPost

PHX = ZoneInfo("America/Phoenix")


def make_post(text: str, post_id: str = "1") -> RawPost:
    return RawPost(
        post_id=post_id,
        text=text,
        created_at=datetime(2026, 6, 1, 9, 0, tzinfo=PHX),
        author_username="test_wholesale_deals",
        url=f"https://x.com/test_wholesale_deals/status/{post_id}",
    )


def test_parses_slash_format_with_full_address():
    post = make_post(
        "1423 E Cactus Rd, Phoenix, AZ 85020. 4/2 1678 ft2. Asking $319,000. ARV $410,000."
    )
    listing = parse_post(post)
    assert listing.address == "1423 E Cactus Rd"
    assert listing.city == "Phoenix"
    assert listing.state == "AZ"
    assert listing.zip_code == "85020"
    assert listing.beds == 4
    assert listing.baths == 2
    assert listing.square_feet == 1678
    assert listing.price == 319000
    assert listing.arv == 410000


def test_parses_labeled_format():
    post = make_post(
        "908 W Glendale Ave, Glendale, AZ 85301. Beds: 3 Baths: 2 Sq Ft: 1450. Price $265,000."
    )
    listing = parse_post(post)
    assert listing.beds == 3
    assert listing.baths == 2
    assert listing.square_feet == 1450
    assert listing.price == 265000


def test_parses_bed_bath_square_ft_words():
    post = make_post("Bed 4 Bath 2 Square Ft 1678 - 1423 E Cactus Rd, Phoenix, AZ 85020.")
    listing = parse_post(post)
    assert listing.beds == 4
    assert listing.baths == 2
    assert listing.square_feet == 1678


def test_roof_and_ac_age_extraction():
    post = make_post("4/2 1678 ft2. Roof replaced 8 yrs ago. AC unit 3 years old.")
    listing = parse_post(post)
    assert listing.age_of_roof == "8 yrs"
    assert listing.age_of_ac == "3 yrs"


def test_unparseable_post_leaves_fields_blank():
    post = make_post(
        "Off market opportunity in Mesa, contact for details. Motivated seller, needs some TLC."
    )
    listing = parse_post(post)
    assert listing.address is None
    assert listing.beds is None
    assert listing.baths is None
    assert listing.square_feet is None
    assert listing.price is None
    # Notes must always contain the full original text
    assert listing.notes == post.text


def test_needs_ai_fallback_true_when_nothing_resolved():
    post = make_post("Off market opportunity, contact for details.")
    listing = parse_post(post)
    assert needs_ai_fallback(listing) is True


def test_needs_ai_fallback_false_when_core_fields_found():
    post = make_post("1423 E Cactus Rd, Phoenix, AZ 85020. 4/2 1678 ft2.")
    listing = parse_post(post)
    assert needs_ai_fallback(listing) is False
