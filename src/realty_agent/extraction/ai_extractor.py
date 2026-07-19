"""AI-assisted extraction, used only as a fallback for posts the
deterministic parser (see :mod:`realty_agent.extraction.parser`) cannot
confidently handle.

Kept provider-agnostic behind a tiny interface so the freelancer /
end-client can point it at Azure OpenAI, the Anthropic API, or any other
chat-completions-style endpoint by supplying a ``complete`` callable --
no code changes required, only configuration (see
``config/settings.example.yaml``: ``ai_provider`` / ``ai_model``).
"""

from __future__ import annotations

import json
from typing import Callable, Optional

from realty_agent.models import ExtractedListing, RawPost

CompletionFn = Callable[[str], str]

_SYSTEM_PROMPT = (
    "You extract structured real estate data from a short social media post. "
    "Return ONLY a compact JSON object with these keys: address, city, state, "
    "zip_code, beds, baths, square_feet, price, arv, age_of_roof, age_of_ac. "
    "Use null for any value that is not clearly present in the text. "
    "Do not guess or infer values that are not supported by the text."
)


def build_prompt(post_text: str) -> str:
    return f'{_SYSTEM_PROMPT}\n\nPost:\n"""\n{post_text}\n"""'


def extract_with_ai(post: RawPost, complete: Optional[CompletionFn]) -> ExtractedListing:
    """Call the configured AI model to extract fields from ``post.text``.

    ``complete`` is a simple ``str -> str`` function so this module has
    zero hard dependency on any specific SDK; wire it up to Azure OpenAI
    or the Anthropic API in ``main.py`` / the Azure Function entry point.
    If no completion function is configured, the post is returned with
    every field blank rather than raising, so the pipeline degrades
    gracefully instead of crashing a scheduled run.
    """
    listing = ExtractedListing(
        post_id=post.post_id,
        post_date_time=post.created_at,
        post_url=post.url,
        notes=post.text,
    )

    if complete is None:
        return listing

    raw_response = complete(build_prompt(post.text))
    try:
        data = json.loads(raw_response)
    except (ValueError, TypeError):
        return listing

    listing.address = data.get("address")
    listing.city = data.get("city")
    listing.state = data.get("state")
    listing.zip_code = data.get("zip_code")
    listing.beds = data.get("beds")
    listing.baths = data.get("baths")
    listing.square_feet = data.get("square_feet")
    listing.price = data.get("price")
    listing.arv = data.get("arv")
    listing.age_of_roof = data.get("age_of_roof")
    listing.age_of_ac = data.get("age_of_ac")
    return listing
