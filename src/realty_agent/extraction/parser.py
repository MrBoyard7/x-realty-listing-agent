"""Deterministic, dependency-light extraction of structured fields from post text.

The project spec calls for minimizing AI token consumption. Real estate
"bed/bath/sqft" shorthand is highly patterned (``4/2``, ``Beds: 4``,
``Bed 4 Bath 2``, ``1678 ft2`` ...), so a rule-based pass can resolve the
large majority of posts without ever calling an AI model. Only posts
that this parser cannot confidently resolve should be escalated to
:mod:`realty_agent.extraction.ai_extractor`.
"""

from __future__ import annotations

import re
from typing import Optional

from realty_agent.models import ExtractedListing, RawPost

_BEDS_BATHS_SLASH = re.compile(r"\b(\d{1,2})\s*/\s*(\d{1,2})\b")
_BEDS_LABEL = re.compile(r"\bbeds?\s*[:\-]?\s*(\d{1,2})\b", re.IGNORECASE)
_BATHS_LABEL = re.compile(r"\bbaths?\s*[:\-]?\s*(\d{1,2}(?:\.\d)?)\b", re.IGNORECASE)
_SQFT_LABEL = re.compile(
    r"\b(?:sq\.?\s*ft\.?|square\s*f(?:ee)?t|ft2|ft\u00b2|sf)\s*[:\-]?\s*(\d{3,6})\b",
    re.IGNORECASE,
)
_SQFT_TRAILING = re.compile(
    r"\b(\d{3,6})\s*(?:sq\.?\s*ft\.?|square\s*f(?:ee)?t|ft2|ft\u00b2|sf)\b",
    re.IGNORECASE,
)
_PRICE_LABEL = re.compile(r"\$\s?([\d,]{4,12})(?:\.\d+)?")
_ARV_LABEL = re.compile(r"\barv\s*[:\-]?\s*\$?\s?([\d,]{4,12})", re.IGNORECASE)
_ROOF_AGE_LABEL = re.compile(r"\broof\D{0,15}?(\d{1,3})\s*(?:yrs?|years?)?\b", re.IGNORECASE)
_AC_AGE_LABEL = re.compile(
    r"\b(?:a\/?c|hvac)\D{0,15}?(\d{1,3})\s*(?:yrs?|years?)?\b", re.IGNORECASE
)

# Very simple US street-address heuristic: number + street name ending in
# a common suffix, optionally followed by ", City, ST 12345". Anchoring on
# the suffix (St/Ave/Rd/...) keeps this from accidentally swallowing an
# unrelated number earlier in the post (e.g. a square-footage figure).
_STREET_SUFFIX = r"(?:St|Ave|Blvd|Dr|Rd|Ln|Ct|Pl|Cir|Way|Pkwy|Hwy)\.?"
_ADDRESS_CORE = (
    r"\d{2,6}\s+(?:[NSEW]\.?\s+)?[A-Za-z][A-Za-z'\-]*(?:\s+[A-Za-z][A-Za-z'\-]*){0,3}?"
    rf"\s+{_STREET_SUFFIX}"
)
_ADDRESS_WITH_CITY_STATE_ZIP = re.compile(
    rf"(?P<address>{_ADDRESS_CORE})"
    r",\s*(?P<city>[A-Za-z .\'\-]{2,40}),\s*(?P<state>[A-Z]{2})\s*(?P<zip>\d{5})?\b"
)
_BARE_ADDRESS = re.compile(_ADDRESS_CORE)


def _to_float(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def _to_int(text: Optional[str]) -> Optional[int]:
    value = _to_float(text)
    return int(value) if value is not None else None


def parse_post(post: RawPost) -> ExtractedListing:
    """Best-effort, rule-based extraction. Never raises; unmatched
    fields are simply left as ``None`` per the spec."""

    text = post.text

    beds: Optional[int] = None
    baths: Optional[float] = None

    slash_match = _BEDS_BATHS_SLASH.search(text)
    beds_label_match = _BEDS_LABEL.search(text)
    baths_label_match = _BATHS_LABEL.search(text)

    if beds_label_match:
        beds = _to_int(beds_label_match.group(1))
    elif slash_match:
        beds = _to_int(slash_match.group(1))

    if baths_label_match:
        baths = _to_float(baths_label_match.group(1))
    elif slash_match:
        baths = _to_float(slash_match.group(2))

    sqft_match = _SQFT_LABEL.search(text) or _SQFT_TRAILING.search(text)
    square_feet = _to_int(sqft_match.group(1)) if sqft_match else None

    # A bare "4/2 2000" pattern (beds/baths sqft with no label at all).
    if square_feet is None and slash_match:
        trailing = text[slash_match.end() :]
        bare_num = re.match(r"\s*,?\s*(\d{3,6})\b", trailing)
        if bare_num:
            square_feet = _to_int(bare_num.group(1))

    price_match = _PRICE_LABEL.search(text)
    price = _to_float(price_match.group(1)) if price_match else None

    arv_match = _ARV_LABEL.search(text)
    arv = _to_float(arv_match.group(1)) if arv_match else None

    roof_match = _ROOF_AGE_LABEL.search(text)
    age_of_roof = f"{roof_match.group(1)} yrs" if roof_match else None

    ac_match = _AC_AGE_LABEL.search(text)
    age_of_ac = f"{ac_match.group(1)} yrs" if ac_match else None

    address = city = state = zip_code = None
    full_match = _ADDRESS_WITH_CITY_STATE_ZIP.search(text)
    if full_match:
        address = full_match.group("address").strip()
        city = full_match.group("city").strip()
        state = full_match.group("state").strip()
        zip_code = full_match.group("zip")
    else:
        bare_match = _BARE_ADDRESS.search(text)
        if bare_match:
            address = bare_match.group(0).strip()

    return ExtractedListing(
        post_id=post.post_id,
        post_date_time=post.created_at,
        post_url=post.url,
        notes=post.text,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        beds=beds,
        baths=baths,
        square_feet=square_feet,
        price=price,
        arv=arv,
        age_of_roof=age_of_roof,
        age_of_ac=age_of_ac,
    )


def needs_ai_fallback(listing: ExtractedListing) -> bool:
    """Decide whether the rule-based pass was confident enough.

    Escalate to the (paid) AI extractor only when the cheap parser could
    not resolve *any* of the core structured fields, keeping token spend
    proportional to how "unstructured" a post actually is.
    """
    core_fields = (listing.beds, listing.baths, listing.square_feet, listing.address)
    return all(value is None for value in core_fields)
