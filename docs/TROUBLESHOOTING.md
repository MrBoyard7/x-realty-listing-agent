# Operating & Troubleshooting Guide

## Normal operation

Each run (every 5 minutes, during the configured operating window):

1. Downloads `listings.xlsx` from OneDrive.
2. Fetches posts newer than the last processed post ID.
3. Parses, enriches, de-duplicates, and inserts/archives rows as needed.
4. Uploads the updated workbook back to OneDrive.
5. Updates the local delta-sync state file with the newest post ID/time.

If there are no new posts, the run finishes quickly with
`posts_seen=0` in the logs and no changes to the workbook.

## Common issues

### `ZoneInfoNotFoundError: No time zone found with key America/Phoenix` (Windows)

Windows does not ship the IANA time zone database that Python's
`zoneinfo` module relies on (Linux and macOS do). Install the `tzdata`
package, which is already listed in `requirements.txt` /
`pyproject.toml` for `sys_platform == "win32"`:

```bash
pip install tzdata
```

Then re-run `pytest`. If you installed the project before this was
added, re-run `pip install -e .` (note the trailing `.` — `pip install
-e` with nothing after it just prints pip's usage text and installs
nothing) to pick up the dependency.

### "Outside operating window -- skipping run" appears in every log

This is expected outside Mon-Fri 6am-6pm America/Phoenix; it is not an
error. Check `config/settings.yaml` (`operating_days`, `operating_start`,
`operating_end`, `timezone`) if the window looks wrong.

### An `Error` row appears in the spreadsheet

Per the project's error-handling design, any unhandled exception during
a run results in a row inserted at position 2 with `Status = Error` and
a message in `Notes` -- rather than crashing silently. Check the
Function App's log stream (Application Insights) for the full stack
trace using the timestamp on the error row to locate the corresponding
log entries.

Common causes:

- **X API errors**: expired/revoked bearer token, rate limiting, or the
  target account changed its username. Verify
  `REALTY_AGENT_X_BEARER_TOKEN` and `REALTY_AGENT_X_USERNAME`.
- **Graph/OneDrive errors**: expired client secret, revoked admin
  consent, or an incorrect `REALTY_AGENT_ONEDRIVE_FILE_PATH`. Verify the
  app registration's certificate/secret is still valid and that
  `Files.ReadWrite.All` consent has not been revoked.

### A listing's fields are unexpectedly blank

This is by design when the post's wording doesn't match a known pattern
and (if enabled) the AI fallback also could not confidently extract a
value -- the spec requires leaving unclear fields blank rather than
guessing. Check the `Notes` column (always the full original post text)
to see exactly what the agent was working from.

### A repost created a duplicate row instead of being ignored

Check whether any of price, ARV, beds, baths, square feet, roof age, or
AC age genuinely differ between the two posts -- these are the fields
that determine a new version per the spec. Minor text rewording alone
should never trigger a new row; if it does, please open an issue with
both post texts so the parsing/matching logic can be adjusted.

### Backfill isn't finding older posts

Confirm the configured `backfill_days` (or the `--backfill-days` CLI
flag / `REALTY_AGENT_BACKFILL_DAYS` app setting) covers the desired
range, and that the X API plan in use actually allows querying that far
back in the account's history.

## Where to look for logs

- **Local runs**: standard output (the CLI entry point configures
  `logging.basicConfig(level=logging.INFO)`).
- **Azure Functions**: Application Insights, filtered to the
  `listing_sync_timer` function, or `func azure functionapp logstream`
  for a live tail during a deployment.
