"""Health insight MVP toolkit.

This package offers utilities for storing daily health data, summarizing it, 
computing global patterns, and managing subjective events for the LLM tooling layer.
"""

from .storage import (
    get_all_days,
    get_day_json,
    save_day_json,
    write_fitbit_data,
    write_manual_event,
)
from .fitbit_api import FitbitAuth, FitbitClient
from .summary import summarize_day
from .similar import find_similar_days
from .global_patterns import compute_global_patterns
from .subjective_events import (
    get_events_by_date,
    load_subjective_events,
    write_subjective_event,
)
from .llm_prompt import SYSTEM_PROMPT

__all__ = [
    "get_all_days",
    "get_day_json",
    "save_day_json",
    "write_fitbit_data",
    "write_manual_event",
    "FitbitAuth",
    "FitbitClient",
    "summarize_day",
    "find_similar_days",
    "compute_global_patterns",
    "load_subjective_events",
    "write_subjective_event",
    "get_events_by_date",
    "SYSTEM_PROMPT",
]
