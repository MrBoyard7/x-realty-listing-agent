"""Single entry point used by both the Azure Function and local CLI runs.

Responsibilities:

1. Check whether "now" is inside the configured operating window.
2. Download the current workbook from OneDrive (if a OneDrive client is
   configured) to a local temp path.
3. Run the delta sync (or backfill) pipeline against the local copy.
4. Upload the modified workbook back to OneDrive.
5. On any error, write an error row instead of letting the run crash
   silently, per the spec's error-handling requirement.
"""

from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from realty_agent.config import Settings
from realty_agent.errors import RealtyAgentError
from realty_agent.scheduler import is_within_operating_window
from realty_agent.storage.excel_writer import ensure_workbook, insert_error_row
from realty_agent.storage.onedrive_client import OneDriveClient
from realty_agent.sync import run_backfill, run_delta_sync
from realty_agent.x_client import MockXClient, XApiClient

logger = logging.getLogger("realty_agent")
logging.basicConfig(level=logging.INFO)


def _build_x_client(settings: Settings):
    if settings.x_bearer_token:
        return XApiClient(bearer_token=settings.x_bearer_token)
    logger.warning("No X bearer token configured -- using MockXClient with sample data.")
    return MockXClient.with_sample_data()


def run(settings: Optional[Settings] = None, backfill_days: Optional[int] = None) -> None:
    settings = settings or Settings.load()
    now = datetime.now(settings.tzinfo)

    if backfill_days is None and not is_within_operating_window(
        now, settings.operating_days, settings.operating_start, settings.operating_end
    ):
        logger.info("Outside operating window (%s) -- skipping run.", now.isoformat())
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        workbook_local = tmp_path / "listings.xlsx"
        state_local = tmp_path / "sync_state.json"

        onedrive: Optional[OneDriveClient] = None
        # In production, construct OneDriveClient from settings/secrets and
        # download/upload around the pipeline call below. Left disabled by
        # default so the project runs fully offline for local dev/tests.

        try:
            if onedrive is not None:
                onedrive.download(settings.onedrive_file_path, workbook_local)
            else:
                ensure_workbook(workbook_local)

            client = _build_x_client(settings)

            if backfill_days is not None:
                result = run_backfill(
                    client, settings.x_username, workbook_local, backfill_days, now=now
                )
            else:
                result = run_delta_sync(client, settings.x_username, workbook_local, state_local)

            logger.info(
                "Sync complete: seen=%s inserted=%s archived=%s duplicates=%s",
                result.posts_seen,
                result.rows_inserted,
                result.rows_archived,
                result.duplicates_ignored,
            )

            if onedrive is not None:
                onedrive.upload(settings.onedrive_file_path, workbook_local)

        except RealtyAgentError as exc:
            logger.exception("Pipeline error during scheduled run")
            ensure_workbook(workbook_local)
            insert_error_row(workbook_local, now, f"{type(exc).__name__}: {exc}")
            if onedrive is not None:
                onedrive.upload(settings.onedrive_file_path, workbook_local)
        except Exception as exc:  # noqa: BLE001 - top-level safety net
            logger.exception("Unexpected error during scheduled run")
            ensure_workbook(workbook_local)
            insert_error_row(workbook_local, now, f"Unexpected error: {exc}")
            if onedrive is not None:
                onedrive.upload(settings.onedrive_file_path, workbook_local)


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the real estate listing agent once.")
    parser.add_argument(
        "--backfill-days",
        type=int,
        default=None,
        help="Process posts from the last N days instead of doing a normal delta sync.",
    )
    args = parser.parse_args()
    run(backfill_days=args.backfill_days)


if __name__ == "__main__":
    _cli()
