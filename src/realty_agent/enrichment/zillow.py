"""Best-effort Zillow property URL construction.

Zillow's canonical URL scheme is
``https://www.zillow.com/homes/<address-slug>_rb/`` which resolves to a
search / property page without requiring an API key. This keeps the
solution simple and free, matching the project's cost-optimization goal.
A private Zillow API integration can be swapped in later without
changing the call site in :mod:`realty_agent.sync.delta_sync`.
"""

from __future__ import annotations

import re
from typing import Optional


def _slugify(*parts: Optional[str]) -> str:
    joined = " ".join(p for p in parts if p)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", joined).strip("-")
    return slug


def build_zillow_url(
    address: Optional[str],
    city: Optional[str],
    state: Optional[str],
    zip_code: Optional[str],
) -> Optional[str]:
    if not address:
        return None
    slug = _slugify(address, city, state, zip_code)
    if not slug:
        return None
    return f"https://www.zillow.com/homes/{slug}_rb/"
