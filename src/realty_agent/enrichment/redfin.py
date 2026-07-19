"""Best-effort RedFin property URL construction.

Mirrors :mod:`realty_agent.enrichment.zillow`: RedFin supports a simple
``https://www.redfin.com/stingray/do/location-autocomplete?...`` search
form, but for a zero-cost, zero-auth link we use RedFin's public search
path which accepts a free-text query and redirects to the closest match.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote_plus


def build_redfin_url(
    address: Optional[str],
    city: Optional[str],
    state: Optional[str],
    zip_code: Optional[str],
) -> Optional[str]:
    if not address:
        return None
    query_parts = [p for p in (address, city, state, zip_code) if p]
    query = quote_plus(" ".join(query_parts))
    return f"https://www.redfin.com/search?query={query}"
