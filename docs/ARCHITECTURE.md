# Architecture

## Overview

```
                 ┌──────────────────────────┐
   every 5 min   │   Azure Function (Timer) │
  ───────────────▶  azure_function/          │
                 │  function_app.py          │
                 └─────────────┬─────────────┘
                               │ calls
                               ▼
                 ┌──────────────────────────┐
                 │   realty_agent.main.run   │
                 │  - checks operating window│
                 │  - downloads workbook      │
                 │  - runs delta sync/backfill│
                 │  - uploads workbook        │
                 │  - writes error row on fail│
                 └─────────────┬─────────────┘
                               │
        ┌──────────────────────┼───────────────────────┐
        ▼                      ▼                        ▼
┌───────────────┐   ┌─────────────────────┐   ┌────────────────────┐
│ x_client       │   │ extraction          │   │ enrichment          │
│ - XApiClient   │──▶│ - parser (regex,    │──▶│ - zillow, redfin    │
│ - MockXClient  │   │   0 AI tokens)      │   │ - county_assessor   │
│                │   │ - ai_extractor      │   │                     │
│                │   │   (fallback only)   │   │                     │
└───────────────┘   └─────────────────────┘   └────────────────────┘
                               │
                               ▼
                 ┌──────────────────────────┐
                 │ dedup.matcher              │
                 │ - normalized address /     │
                 │   parcel matching           │
                 │ - new / duplicate / version │
                 │   decision                  │
                 └─────────────┬─────────────┘
                               ▼
                 ┌──────────────────────────┐
                 │ storage.excel_writer      │
                 │ - insert at row 2          │
                 │ - archive previous version │
                 │ - error rows               │
                 └──────────────────────────┘
                               │
                               ▼
                 ┌──────────────────────────┐
                 │ storage.onedrive_client    │
                 │ (Microsoft Graph, app-only)│
                 └──────────────────────────┘
```

## Why this shape

- **Deterministic parsing first.** `extraction/parser.py` resolves the
  large majority of posts with plain regex, at zero AI cost. Only posts
  where none of the core fields (beds/baths/sqft/address) can be
  confidently resolved are escalated to `extraction/ai_extractor.py`,
  which is provider-agnostic (Azure OpenAI, Anthropic API, or any other
  chat-completion endpoint can be wired in via a single `complete`
  callable in `main.py`).

- **Local file, not live Graph calls, for every mutation.** The workbook
  is downloaded once per run, mutated locally with `openpyxl`
  (`storage/excel_writer.py`), and uploaded once. This keeps row
  insertion fast and avoids rate-limiting the Graph API with dozens of
  small requests per run.

- **Only active rows are ever matched or re-evaluated.** `Archive`d rows
  are excluded from `read_active_rows()`, which is what keeps both the
  matching pass and (if AI is used) the AI token spend from growing
  linearly with the size of the historical sheet.

- **Operating-window enforcement lives in code, not in the timer CRON
  expression.** The Azure Function timer fires every 5 minutes every
  day; `scheduler/time_window.py` decides whether "now" is actually a
  configured working day/hour before doing any work. This is what makes
  the days/hours configurable without redeploying.

- **Delta sync state is a small JSON file** (`sync/state.py`) tracking
  the last processed post id + timestamp, stored next to the workbook so
  it travels with the same backup/versioning as the data it describes.

## Error handling flow

Any exception raised inside the pipeline during a scheduled run is caught
in `main.run()`, which then calls `storage.excel_writer.insert_error_row`
to add a row at position 2 with `Status = Error` and a message in
`Notes`, and re-uploads the workbook. No exception should ever cause a
scheduled run to fail silently or crash without a trace in the sheet.
