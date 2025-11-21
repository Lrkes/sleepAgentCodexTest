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
    SYSTEM_PROMPT,
)
```
