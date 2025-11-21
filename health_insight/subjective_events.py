from __future__ import annotations

import json
import uuid
from typing import Dict, List

from .storage import SUBJECTIVE_EVENTS_PATH


def load_subjective_events() -> List[Dict]:
    """Load all subjective events from storage."""
    if not SUBJECTIVE_EVENTS_PATH.exists():
        return []
    with SUBJECTIVE_EVENTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_subjective_event(event_data: Dict) -> Dict:
    """Append a subjective event to the collection and persist it."""
    events = load_subjective_events()
    if "id" not in event_data:
        event_data["id"] = str(uuid.uuid4())
    events.append(event_data)
    SUBJECTIVE_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SUBJECTIVE_EVENTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)
    return event_data


def get_events_by_date(date_str: str) -> List[Dict]:
    """Retrieve all subjective events for a specific date."""
    return [event for event in load_subjective_events() if event.get("date") == date_str]


__all__ = ["load_subjective_events", "write_subjective_event", "get_events_by_date"]
