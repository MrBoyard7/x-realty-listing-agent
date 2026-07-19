"""Core data structures shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ListingStatus(str, Enum):
    """Allowed values for the ``Status`` column."""

    NEW = "New"
    LIKE = "Like"
    ARCHIVE = "Archive"
    ERROR = "Error"


#: Ordered column headers expected in row 1 of the workbook.
EXCEL_COLUMNS = [
    "Post Date/Time",
    "Post Date",
    "Post Time",
    "X Post ID",
    "X Post URL",
    "Status",
    "Address",
    "City",
    "State",
    "ZIP",
    "County",
    "Parcel Number",
    "Beds",
    "Baths",
    "Square Feet",
    "Price",
    "ARV",
    "Age of Roof",
    "Age of AC",
    "Google Docs URL",
    "Zillow URL",
    "RedFin URL",
    "County Assessor URL",
    "Notes",
]


@dataclass
class RawPost:
    """A single post as returned by the X client, before extraction."""

    post_id: str
    text: str
    created_at: datetime  # timezone-aware, America/Phoenix
    author_username: str
    url: str


@dataclass
class ExtractedListing:
    """Structured fields pulled out of a :class:`RawPost`.

    Every field except ``post_id``, ``post_date_time``, ``post_url`` and
    ``notes`` is optional: when a value cannot reasonably be inferred from
    the post text it must be left blank (``None``), per the project spec.
    """

    post_id: str
    post_date_time: datetime
    post_url: str
    notes: str

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    county: Optional[str] = None
    parcel_number: Optional[str] = None

    beds: Optional[float] = None
    baths: Optional[float] = None
    square_feet: Optional[int] = None
    price: Optional[float] = None
    arv: Optional[float] = None
    age_of_roof: Optional[str] = None
    age_of_ac: Optional[str] = None

    google_docs_url: Optional[str] = None
    zillow_url: Optional[str] = None
    redfin_url: Optional[str] = None
    county_assessor_url: Optional[str] = None

    status: ListingStatus = ListingStatus.NEW

    def normalized_address(self) -> Optional[str]:
        """Return a normalized version of the address used for de-duplication.

        Normalization is intentionally simple and dependency-free: lower
        case, collapse whitespace, and strip common punctuation and unit
        abbreviations that do not change the identity of the property.
        """
        if not self.address:
            return None
        import re

        text = self.address.lower().strip()
        text = re.sub(r"[.,#]", " ", text)
        replacements = {
            r"\bstreet\b": "st",
            r"\bavenue\b": "ave",
            r"\bboulevard\b": "blvd",
            r"\bdrive\b": "dr",
            r"\broad\b": "rd",
            r"\blane\b": "ln",
            r"\bcourt\b": "ct",
            r"\bplace\b": "pl",
            r"\bcircle\b": "cir",
            r"\bapartment\b": "apt",
            r"\bunit\b": "apt",
        }
        for pattern, repl in replacements.items():
            text = re.sub(pattern, repl, text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def meaningful_attributes(self) -> tuple:
        """Attributes that, if changed, mean a repost is a new *version*.

        Per the spec, differences in post id/url/date/time or minor
        formatting must NOT trigger a new version -- only real property
        attribute changes should. The raw ``notes`` text is deliberately
        excluded here: it holds the complete original post, which will
        almost always be worded differently between a first post and a
        later repost even when nothing about the property itself
        changed, so comparing it verbatim would produce false "new
        version" results on harmless rewording.
        """
        return (
            self.price,
            self.arv,
            self.beds,
            self.baths,
            self.square_feet,
            self.age_of_roof,
            self.age_of_ac,
        )
