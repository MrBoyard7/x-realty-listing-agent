# X Realty Listing Agent

[![CI](https://github.com/MrBoyard7/x-realty-listing-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/MrBoyard7/x-realty-listing-agent/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/MrBoyard7/x-realty-listing-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/MrBoyard7/x-realty-listing-agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Azure Functions](https://img.shields.io/badge/Azure-Functions-0062AD?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/en-us/products/functions)
[![Microsoft Graph](https://img.shields.io/badge/Microsoft-Graph%20API-0078D4?logo=microsoft&logoColor=white)](https://learn.microsoft.com/en-us/graph/)

A low-cost, low-maintenance agent that reads real estate listing posts
from a configured X (Twitter) account and turns them into structured
rows in an Excel workbook stored on Microsoft OneDrive -- built around
Azure Functions and Microsoft Graph, with AI extraction used only as a
fallback for posts a deterministic parser can't confidently handle.

> This repository is a demonstration/portfolio build showing the
> architecture and implementation approach for this kind of project. It
> ships with a fully working pipeline exercised end-to-end against a
> local mock X client and sample posts (see `sample_data/`); the real
> X API and Microsoft Graph clients are implemented and documented in
> `docs/SETUP.md` for connecting to a live test or production account.

## Features

- **Cheap-first extraction.** A regex-based parser resolves the common
  post formats (`4/2`, `Beds: 4 Baths: 2 Sq Ft: 1678`, `Bed 4 Bath 2
  Square Ft 1678`, etc.) with zero AI token cost; an AI fallback only
  kicks in for posts it can't confidently parse.
- **Configurable schedule.** Operating days/hours/timezone/backfill are
  all read from `config/settings.yaml` (or environment variables) --
  never hard-coded.
- **Smart de-duplication & versioning.** Matches properties by
  normalized address (and parcel number when available); reposts with
  no meaningful attribute change are ignored, reposts with real changes
  (price, ARV, specs, roof/AC age) create a new row and archive the
  previous one.
- **Token/cost-aware.** Archived rows are excluded from every matching
  pass, so cost doesn't grow with sheet history.
- **Zillow / RedFin / county assessor links** generated automatically
  from the parsed address.
- **Graceful error handling.** Any failure during a scheduled run
  becomes a visible `Error` row in the sheet instead of a silent crash.

## Project layout

```
x-realty-listing-agent/
├── azure_function/            # Azure Functions app (timer trigger)
│   ├── function_app.py
│   ├── host.json
│   └── local.settings.json.example
├── config/
│   ├── settings.example.yaml  # all non-secret, user-editable settings
│   └── settings.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── COSTS.md
│   └── TROUBLESHOOTING.md
├── sample_data/
│   └── sample_posts.json      # demo posts covering every documented format
├── src/realty_agent/
│   ├── config.py              # Settings loader (YAML + env overrides)
│   ├── models.py               # RawPost / ExtractedListing / Excel columns
│   ├── errors.py
│   ├── main.py                 # entry point (CLI + Azure Function share this)
│   ├── x_client/
│   │   ├── base.py             # XClient interface
│   │   ├── mock_client.py      # in-memory client for dev/tests/demos
│   │   └── x_api_client.py     # real X API v2 client
│   ├── extraction/
│   │   ├── parser.py           # deterministic, zero-token extraction
│   │   └── ai_extractor.py     # provider-agnostic AI fallback
│   ├── enrichment/
│   │   ├── zillow.py
│   │   ├── redfin.py
│   │   ├── county_assessor.py
│   │   └── county_data.json    # editable city→county→assessor-URL tables
│   ├── dedup/
│   │   └── matcher.py          # address/parcel matching + version decisions
│   ├── storage/
│   │   ├── excel_writer.py     # openpyxl read/write helpers
│   │   └── onedrive_client.py  # Microsoft Graph client (app-only auth)
│   ├── sync/
│   │   ├── state.py            # delta-sync high-water-mark tracking
│   │   └── delta_sync.py       # orchestrates the full pipeline
│   └── scheduler/
│       └── time_window.py      # operating-day/hour check
├── tests/                       # pytest suite, one file per module above
├── .github/workflows/ci.yml     # lint + type-check + test + coverage
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
└── README.md  (this file)
```

See `docs/ARCHITECTURE.md` for a data-flow diagram and the reasoning
behind these choices.

## Quick start (fully offline demo)

```bash
git clone https://github.com/MrBoyard7/x-realty-listing-agent.git
cd x-realty-listing-agent

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt
pip install -e .

# Run the pipeline once against the bundled sample posts (no X/Azure
# credentials needed -- it automatically falls back to a mock client):
python -m realty_agent.main --backfill-days 7
```

## Running the tests

```bash
pytest                    # unit tests + coverage report (see pyproject.toml)
black --check src tests   # formatting
flake8 src tests          # linting
mypy src                  # type checking
```

All four checks also run automatically in CI on every push/PR (see the
CI badge above).

## Connecting to a real X account and OneDrive

See **[docs/SETUP.md](docs/SETUP.md)** for:

- Creating a private test X account and X API credentials.
- Registering an Azure AD app with `Files.ReadWrite.All` for
  Microsoft Graph / OneDrive access.
- Deploying to Azure Functions and configuring app settings.
- Moving from a test account to the production account without ever
  sharing its password.

Expected operating costs are broken down in
**[docs/COSTS.md](docs/COSTS.md)**, and common operational issues are
covered in **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**.

## License

Released under the [MIT License](LICENSE).

Copyright (c) 2026 Prince Boyard MBOUNGOU NGOMA
