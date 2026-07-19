# Expected Operating Costs

Estimates below assume the configured schedule (every 5 minutes, Mon-Fri,
6am-6pm America/Phoenix -- 144 runs/day, ~3,120 runs/month) and a low
posting volume typical of a single wholesaler account. Actual costs
depend on your Azure region, X API plan, and chosen AI provider; treat
these as planning-level estimates, not a quote.

## Azure Functions (Consumption plan)

- Each run is a short-lived timer trigger (typically well under a
  second of compute when there are no new posts, and a few seconds when
  there are).
- At this volume, execution time and memory usage stay comfortably
  within the Azure Functions Consumption plan's **monthly free grant**
  (1M executions / 400,000 GB-s), so expect **$0/month** for compute in
  the common case, with only storage/bandwidth as a marginal cost.

## Microsoft Graph / OneDrive

- No separate charge beyond an existing Microsoft 365 subscription that
  already includes OneDrive; Graph API calls themselves are free.

## Azure AD App Registration

- Free; no cost associated with the app registration or client secret.

## AI extraction (only for posts the rule-based parser cannot resolve)

- Because the deterministic parser (`extraction/parser.py`) is tried
  first and handles the large majority of the documented post formats,
  AI calls should be rare -- reserved for genuinely unstructured posts.
- Using a small, low-cost model (e.g. Azure OpenAI's smallest GPT-4o
  mini-class deployment, or Claude Haiku) for the occasional fallback
  call, at a few hundred input/output tokens per call, typically costs
  well under **$1-2/month** for a single-account, low-volume use case.
- If AI usage is disabled entirely (`ai_provider: "none"` in
  `config/settings.yaml`), this cost is **$0**, at the expense of
  leaving unparseable posts' structured fields blank.

## X API

- Reading a single account's posts on a schedule requires an X API
  developer plan with read access to the "user tweet timeline" endpoint.
  As of this writing the **Free** tier's read limits are generally too
  low for 5-minute polling in production; a **Basic** tier subscription
  is the more realistic minimum. Confirm current tier pricing and rate
  limits directly at <https://developer.x.com/en/portal/products> before
  committing, as X's API pricing changes periodically.

## Summary

| Component | Typical monthly cost |
|---|---|
| Azure Functions (Consumption) | $0 (within free grant) |
| Microsoft Graph / OneDrive | $0 (uses existing M365 subscription) |
| Azure AD App Registration | $0 |
| AI extraction fallback | $0-2 |
| X API subscription | Depends on current X API tier pricing |

The dominant recurring cost for this project is almost always the X API
subscription tier required for scheduled polling access, not the
Microsoft/Azure/AI portions of the stack.
