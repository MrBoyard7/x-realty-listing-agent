from datetime import datetime
from zoneinfo import ZoneInfo

from realty_agent.dedup.matcher import MatchDecision, decide, find_matching_row
from realty_agent.models import ExtractedListing, ListingStatus

PHX = ZoneInfo("America/Phoenix")


def make_listing(**overrides) -> ExtractedListing:
    defaults = dict(
        post_id="2",
        post_date_time=datetime(2026, 6, 1, 11, 0, tzinfo=PHX),
        post_url="https://x.com/x/status/2",
        notes="4/2 1678 ft2. Price $305,000. ARV $410,000.",
        address="1423 E Cactus Rd",
        city="Phoenix",
        state="AZ",
        beds=4,
        baths=2,
        square_feet=1678,
        price=305000,
        arv=410000,
        age_of_roof="8 yrs",
        age_of_ac="3 yrs",
    )
    defaults.update(overrides)
    return ExtractedListing(**defaults)


EXISTING_ROW = {
    "_row_index": 2,
    "Status": ListingStatus.NEW.value,
    "Address": "1423 e cactus rd",
    "Parcel Number": None,
    "Price": 319000,
    "ARV": 410000,
    "Beds": 4,
    "Baths": 2,
    "Square Feet": 1678,
    "Age of Roof": "8 yrs",
    "Age of AC": "3 yrs",
    "Notes": (
        "1423 E Cactus Rd, Phoenix, AZ 85020. 4/2 1678 ft2. Asking $319,000. "
        "ARV $410,000. Roof approx 8 yrs. AC 3 yrs. Great flip candidate!"
    ),
}


def test_no_match_is_new_property():
    listing = make_listing(address="Somewhere Else Dr")
    match = find_matching_row(listing, [EXISTING_ROW])
    assert match is None
    assert decide(listing, match) == MatchDecision.NEW_PROPERTY


def test_matching_address_with_price_change_is_new_version():
    listing = make_listing()  # price 305000 differs from existing 319000
    match = find_matching_row(listing, [EXISTING_ROW])
    assert match is EXISTING_ROW
    assert decide(listing, match) == MatchDecision.NEW_VERSION


def test_matching_address_no_meaningful_change_is_ignored():
    identical_row = dict(EXISTING_ROW)
    identical_row["Price"] = 305000
    identical_row["Notes"] = "4/2 1678 ft2. Price $305,000. ARV $410,000."
    listing = make_listing()
    match = find_matching_row(listing, [identical_row])
    assert decide(listing, match) == MatchDecision.IGNORE_DUPLICATE


def test_archived_rows_are_never_matched():
    archived_row = dict(EXISTING_ROW)
    archived_row["Status"] = ListingStatus.ARCHIVE.value
    listing = make_listing()
    match = find_matching_row(listing, [archived_row])
    assert match is None


def test_parcel_number_takes_priority_over_address():
    listing = make_listing(address="Different Address Ln", parcel_number="123-45-678")
    row = dict(EXISTING_ROW)
    row["Parcel Number"] = "123-45-678"
    match = find_matching_row(listing, [row])
    assert match is row


def test_post_id_and_date_differences_alone_do_not_trigger_new_version():
    identical_row = dict(EXISTING_ROW)
    identical_row["Price"] = 305000
    identical_row["Notes"] = "4/2 1678 ft2. Price $305,000. ARV $410,000."
    # Different post id / url / date than the row that was originally
    # inserted -- per spec this alone must not create a new version.
    listing = make_listing(post_id="999", post_url="https://x.com/x/status/999")
    match = find_matching_row(listing, [identical_row])
    assert decide(listing, match) == MatchDecision.IGNORE_DUPLICATE
