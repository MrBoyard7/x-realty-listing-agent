"""Property identity matching and repost/version decisions.

Implements the spec's duplicate-handling rules:

* Same property is identified primarily by normalized address, and
  secondarily by parcel number when available.
* A repost with no meaningful attribute changes is ignored outright.
* A repost with a meaningful attribute change becomes a new row
  (Status=New) and the previous active row is archived (Status=Archive).
* Only "active" rows (Status in New/Like/blank) are considered when
  matching -- archived rows are never re-evaluated, which is what keeps
  AI/token spend bounded as the sheet grows.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable, Optional

from realty_agent.models import ExtractedListing, ListingStatus

ACTIVE_STATUSES = {ListingStatus.NEW, ListingStatus.LIKE, None, ""}


class MatchDecision(str, Enum):
    NEW_PROPERTY = "new_property"  # no existing match -> insert as new
    IGNORE_DUPLICATE = "ignore_duplicate"  # matches, nothing meaningful changed
    NEW_VERSION = "new_version"  # matches, something meaningful changed


def is_active(status: Optional[str]) -> bool:
    return status in ACTIVE_STATUSES


def find_matching_row(listing: ExtractedListing, existing_rows: Iterable[dict]) -> Optional[dict]:
    """Find the active existing row that represents the same property.

    ``existing_rows`` are plain dicts keyed by the Excel column names
    (as read back from the workbook), restricted by the caller to active
    rows only before calling this function for cost/token efficiency.
    """
    target_address = listing.normalized_address()
    target_parcel = (listing.parcel_number or "").strip().lower() or None

    for row in existing_rows:
        if not is_active(row.get("Status")):
            continue
        row_parcel = (row.get("Parcel Number") or "").strip().lower() or None
        if target_parcel and row_parcel and target_parcel == row_parcel:
            return row
        row_address = (row.get("Address") or "").strip().lower()
        if target_address and row_address:
            # existing rows already store the normalized address in the
            # Address column's underlying source data; compare directly.
            if row_address == target_address:
                return row
    return None


def decide(listing: ExtractedListing, matching_row: Optional[dict]) -> MatchDecision:
    if matching_row is None:
        return MatchDecision.NEW_PROPERTY

    existing_attrs = (
        matching_row.get("Price"),
        matching_row.get("ARV"),
        matching_row.get("Beds"),
        matching_row.get("Baths"),
        matching_row.get("Square Feet"),
        matching_row.get("Age of Roof"),
        matching_row.get("Age of AC"),
    )
    if listing.meaningful_attributes() == existing_attrs:
        return MatchDecision.IGNORE_DUPLICATE
    return MatchDecision.NEW_VERSION
