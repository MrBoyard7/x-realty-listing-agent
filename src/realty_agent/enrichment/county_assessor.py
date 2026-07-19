"""Determine a property's county and the matching assessor website.

The lookup tables live in ``county_data.json`` next to this module so
they can be extended by a non-developer (just add a JSON entry) without
touching Python code, in the spirit of the project's "configurable
without modifying source code" requirement. Coverage starts with
Arizona (matching the project's America/Phoenix schedule) but the shape
of the data supports any state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

_DATA_PATH = Path(__file__).with_name("county_data.json")


def _load_data() -> dict:
    with open(_DATA_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


_DATA = _load_data()


def _key(city: Optional[str], state: Optional[str]) -> Optional[str]:
    if not city or not state:
        return None
    return f"{city.strip().lower()}, {state.strip().lower()}"


def resolve_county(city: Optional[str], state: Optional[str]) -> Optional[str]:
    """Return the county name for a given city/state, if known."""
    key = _key(city, state)
    if key is None:
        return None
    return _DATA["city_to_county"].get(key)


def resolve_assessor_url(county: Optional[str], state: Optional[str]) -> Optional[str]:
    """Return the county assessor's main property-search URL, if known."""
    if not county or not state:
        return None
    key = f"{county.strip().lower()}, {state.strip().lower()}"
    return _DATA["county_assessor_url"].get(key)


def resolve_county_and_assessor_url(
    city: Optional[str], state: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    county = resolve_county(city, state)
    url = resolve_assessor_url(county, state)
    return county, url
