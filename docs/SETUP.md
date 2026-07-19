# Setup & Deployment

## 1. Local development (using the mock X client and sample data)

```bash
git clone https://github.com/MrBoyard7/x-realty-listing-agent.git
cd x-realty-listing-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .

cp config/settings.example.yaml config/settings.yaml
# settings.yaml already has sensible local defaults

python -m realty_agent.main --backfill-days 7
```

With no `REALTY_AGENT_X_BEARER_TOKEN` set, the pipeline automatically
falls back to `MockXClient.with_sample_data()` (see
`sample_data/sample_posts.json`), which lets you exercise the entire
pipeline -- parsing, de-duplication, versioning, Excel writing -- fully
offline. A local `listings.xlsx` is created in a temp directory; check
the log output for the summary of rows inserted/archived/ignored.

## 2. Setting up a private test X account

1. Create a new, private X account dedicated to testing (do **not** use
   the production account's credentials anywhere in this project).
2. Apply for a Free or Basic tier X API developer account at
   <https://developer.x.com>.
3. Generate a Bearer Token for that developer app.
4. Post a handful of sample listings to the test account, using the
   formats in the project spec (`4/2`, `Beds: 4 Baths: 2 Sq Ft: 1678`,
   etc.) -- or reuse the text in `sample_data/sample_posts.json`.
5. Set `REALTY_AGENT_X_USERNAME` to the test account's handle and
   `REALTY_AGENT_X_BEARER_TOKEN` to the token from step 3.

## 3. Microsoft Graph / OneDrive app registration (for real Excel writes)

1. In the Azure Portal, go to **Azure Active Directory → App
   registrations → New registration**. Any name is fine (e.g.
   `x-realty-listing-agent`).
2. Under **API permissions**, add **Microsoft Graph → Application
   permissions → Files.ReadWrite.All**, then grant admin consent.
3. Under **Certificates & secrets**, create a new client secret and copy
   its value immediately (it will not be shown again).
4. Note the **Tenant ID**, **Application (client) ID**, and the client
   secret value -- these become `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`,
   and `AZURE_CLIENT_SECRET`.
5. Find the target **drive ID** (the OneDrive or SharePoint document
   library that will hold `listings.xlsx`) via
   `GET https://graph.microsoft.com/v1.0/me/drive` (for a personal
   OneDrive) or the equivalent SharePoint site endpoint, and set
   `REALTY_AGENT_ONEDRIVE_DRIVE_ID`.
6. Set `REALTY_AGENT_ONEDRIVE_FILE_PATH` to the path of the workbook
   inside that drive, e.g. `/RealEstate/listings.xlsx`.

`storage/onedrive_client.py` implements the client-credentials flow
against these values. Wiring it into `main.py`'s `run()` function is a
single `OneDriveClient(...)` construction plus the two `download`/
`upload` calls that are already stubbed there with comments.

## 4. Deploying to Azure Functions

```bash
# from the repo root
func azure functionapp publish <YOUR_FUNCTION_APP_NAME> --python
```

Configure the following Application Settings on the Function App (Portal
→ Function App → Configuration), matching `azure_function/local.settings.json.example`:

| Setting | Purpose |
|---|---|
| `REALTY_AGENT_X_USERNAME` | X handle to monitor |
| `REALTY_AGENT_X_BEARER_TOKEN` | X API bearer token |
| `REALTY_AGENT_ONEDRIVE_DRIVE_ID` | Target OneDrive/SharePoint drive |
| `REALTY_AGENT_ONEDRIVE_FILE_PATH` | Path to the workbook in that drive |
| `AZURE_TENANT_ID` / `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` | Graph app registration |
| `REALTY_AGENT_BACKFILL_DAYS` | Optional: run a one-off backfill |

## 5. Moving from test to production

- Swap `REALTY_AGENT_X_USERNAME` / `REALTY_AGENT_X_BEARER_TOKEN` to the
  production values once the client has generated their own API
  credentials for the private production account -- the freelancer
  never needs to see or store that account's password.
- Point `REALTY_AGENT_ONEDRIVE_FILE_PATH` at the production workbook.
- Run once with `--backfill-days N` (or the `REALTY_AGENT_BACKFILL_DAYS`
  app setting) to populate history before turning on the regular 5-minute
  timer trigger.

## 6. Running the test suite

```bash
pytest                 # unit tests + coverage report
black --check src tests
flake8 src tests
mypy src
```
