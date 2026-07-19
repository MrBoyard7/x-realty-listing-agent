"""End-to-end pipeline: fetch posts -> extract -> enrich -> de-dup -> write.

This module wires together every other package but contains no
transport-specific logic itself (no direct HTTP, no direct Graph calls),
which is what makes it straightforward to unit test with
:class:`~realty_agent.x_client.mock_client.MockXClient` and a temporary
workbook file.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from realty_agent.dedup import MatchDecision, decide, find_matching_row
from realty_agent.enrichment import (
    build_redfin_url,
    build_zillow_url,
    resolve_county_and_assessor_url,
)
from realty_agent.extraction import extract_with_ai, needs_ai_fallback, parse_post
from realty_agent.extraction.ai_extractor import CompletionFn
from realty_agent.models import ExtractedListing, ListingStatus, RawPost
from realty_agent.storage.excel_writer import insert_row_at_top, read_active_rows, set_row_status
from realty_agent.sync.state import SyncState
from realty_agent.x_client.base import XClient


@dataclass
class SyncResult:
    posts_seen: int = 0
    rows_inserted: int = 0
    rows_archived: int = 0
    duplicates_ignored: int = 0


def _enrich(listing: ExtractedListing) -> ExtractedListing:
    county, assessor_url = resolve_county_and_assessor_url(listing.city, listing.state)
    listing.county = listing.county or county
    listing.county_assessor_url = assessor_url
    listing.zillow_url = build_zillow_url(
        listing.address, listing.city, listing.state, listing.zip_code
    )
    listing.redfin_url = build_redfin_url(
        listing.address, listing.city, listing.state, listing.zip_code
    )
    return listing


def _extract(post: RawPost, ai_complete: Optional[CompletionFn]) -> ExtractedListing:
    listing = parse_post(post)
    if needs_ai_fallback(listing):
        listing = extract_with_ai(post, ai_complete)
    return _enrich(listing)


def process_posts(
    posts: List[RawPost],
    workbook_path: Path,
    ai_complete: Optional[CompletionFn] = None,
) -> SyncResult:
    """Apply the full pipeline to a batch of already-fetched posts.

    ``posts`` should be newest-first (matches what the X client
    returns) so that inserting each one at row 2 in order preserves
    descending order in the sheet.
    """
    result = SyncResult()
    # Oldest-first so the very newest post ends up physically at row 2.
    for post in sorted(posts, key=lambda p: p.created_at):
        result.posts_seen += 1
        listing = _extract(post, ai_complete)

        active_rows = read_active_rows(workbook_path)
        match = find_matching_row(listing, active_rows)
        decision = decide(listing, match)

        if decision == MatchDecision.IGNORE_DUPLICATE:
            result.duplicates_ignored += 1
            continue

        if decision == MatchDecision.NEW_VERSION and match is not None:
            set_row_status(workbook_path, match["_row_index"], ListingStatus.ARCHIVE)
            result.rows_archived += 1

        insert_row_at_top(workbook_path, listing, ListingStatus.NEW)
        result.rows_inserted += 1

    return result


def run_delta_sync(
    client: XClient,
    username: str,
    workbook_path: Path,
    state_path: Path,
    ai_complete: Optional[CompletionFn] = None,
) -> SyncResult:
    """Fetch only posts newer than the last processed post and process them."""
    state = SyncState.load(state_path)
    posts = client.fetch_recent_posts(username, since_id=state.last_post_id)
    result = process_posts(posts, workbook_path, ai_complete)

    if posts:
        newest = max(posts, key=lambda p: p.created_at)
        state.update(newest.post_id, newest.created_at)
        state.save(state_path)

    return result


def run_backfill(
    client: XClient,
    username: str,
    workbook_path: Path,
    days: int,
    now: Optional[datetime] = None,
    ai_complete: Optional[CompletionFn] = None,
) -> SyncResult:
    """Process posts from the previous ``days`` days, per the spec's
    configurable-backfill requirement."""
    now = now or datetime.now()
    since = now - timedelta(days=days)
    posts = client.fetch_posts_since(username, since)
    return process_posts(posts, workbook_path, ai_complete)
