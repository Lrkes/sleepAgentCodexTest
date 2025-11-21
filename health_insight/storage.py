from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path("data")
DAILY_DIR = DATA_DIR / "daily"
SUBJECTIVE_EVENTS_PATH = DATA_DIR / "subjective_events.json"
GLOBAL_PATTERNS_PATH = DATA_DIR / "global_patterns.json"


def _ensure_daily_dir() -> None:
    DAILY_DIR.mkdir(parents=True, exist_ok=True)


def save_day_json(date_str: str, day_data: Dict) -> Path:
    """Save a day's data dictionary as a JSON file named by date.

    Parameters
    ----------
    date_str: str
        Date string used for the filename (e.g., "2025-02-10").
    day_data: Dict
        Data dictionary that will be serialized.
    """
    _ensure_daily_dir()
    day_data.setdefault("date", date_str)
    filepath = DAILY_DIR / f"{date_str}.json"
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(day_data, f, indent=2)
    return filepath


def get_day_json(date_str: str) -> Optional[Dict]:
    """Load and return the day's data dictionary from JSON file."""
    filepath = DAILY_DIR / f"{date_str}.json"
    if not filepath.exists():
        return None
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_all_days() -> List[Dict]:
    """Load all daily JSON files sorted by date string."""
    if not DAILY_DIR.exists():
        return []
    days: List[Dict] = []
    for filename in sorted(DAILY_DIR.iterdir()):
        if filename.suffix == ".json":
            with filename.open("r", encoding="utf-8") as f:
                days.append(json.load(f))
    return days


def write_manual_event(date_str: str, manual_data: Dict) -> Dict:
    """Merge manual input data into the day's JSON entry.

    If the day entry exists, update its "manual" field; otherwise, create a new entry.
    The manual sub-dictionary is merged to preserve existing keys.
    """
    day = get_day_json(date_str) or {"date": date_str, "fitbit": {}, "manual": {}}
    day.setdefault("fitbit", {})
    day.setdefault("manual", {})
    day["manual"].update(manual_data)
    save_day_json(date_str, day)
    return day


def write_fitbit_data(date_str: str, fitbit_data: Dict) -> Dict:
    """Merge fitbit data into the day's JSON entry."""
    day = get_day_json(date_str) or {"date": date_str, "fitbit": {}, "manual": {}}
    day.setdefault("fitbit", {})
    day.setdefault("manual", {})
    day["fitbit"].update(fitbit_data)
    save_day_json(date_str, day)
    return day


__all__ = [
    "DATA_DIR",
    "DAILY_DIR",
    "SUBJECTIVE_EVENTS_PATH",
    "GLOBAL_PATTERNS_PATH",
    "save_day_json",
    "get_day_json",
    "get_all_days",
    "write_manual_event",
    "write_fitbit_data",
]
