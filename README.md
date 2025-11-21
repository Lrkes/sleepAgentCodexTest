# Health Insight MVP Toolkit

This repository provides a lightweight Python module that stores daily health data
in JSON files, generates summaries, finds similar days, computes global patterns,
and maintains subjective events for an LLM-enabled assistant.

## Key components
- **Daily storage**: Save and retrieve per-day JSON documents under `data/daily/`.
- **Manual & Fitbit merging**: Upsert manual entries or Fitbit metrics without
  overwriting existing fields.
- **Day summaries**: Flag key conditions like short sleep, low HRV, high stress,
  anxiety, and late caffeine.
- **Similar day lookup**: Find historical days sharing the same flagged patterns.
- **Global patterns**: Compute averages, caffeine/sleep correlation, and common
  triggers on stressful days.
- **Subjective events**: Append free-form events with tags and retrieve them by date.
- **LLM prompt**: A ready-to-use system prompt describing tool usage and safety guardrails.

## Quickstart
```bash
python -m compileall health_insight
```

Import the helpers in your agent code:
```python
from health_insight import (
    compute_global_patterns,
    find_similar_days,
    get_all_days,
    get_day_json,
    summarize_day,
    write_fitbit_data,
    write_manual_event,
    write_subjective_event,
    get_events_by_date,
    FitbitAuth,
    FitbitClient,
    SYSTEM_PROMPT,
)
```

### Pulling Fitbit data
1) Create a Fitbit application to obtain a **client id** and **client secret**.
2) Generate a refresh token (one-time OAuth flow) using the built-in helper:
   ```bash
   python -m health_insight.auth_flow --scopes activity heartrate sleep
   ```
   The script starts a localhost listener, opens the Fitbit consent page, captures the
   redirect code, exchanges it for tokens, and writes the resulting credentials to `.env`
   (you can change the target file via `--env-file`). Source the file or export the
   variables before making API calls.
3) Fetch and persist a single day of data:
   ```python
   from datetime import date
   from health_insight import FitbitAuth, FitbitClient

   auth = FitbitAuth.from_env()
   client = FitbitClient(auth)

   day = date.today().isoformat()
   bundle = client.fetch_and_store_daily(day)
   print(bundle)  # activity, sleep, and HRV JSON from Fitbit
   ```

`FitbitClient.refresh_access_token` accepts an optional callback to save the new
`access_token` and `refresh_token` whenever a refresh occurs:

```python
def persist_tokens(token_payload):
    # token_payload includes access_token, refresh_token, expires_in, etc.
    # Save them to your secrets store.
    ...

client.refresh_access_token(on_update=persist_tokens)
```
