from __future__ import annotations

from typing import Dict, Optional

SLEEP_SHORT_THRESHOLD = 6.0
HRV_LOW_THRESHOLD = 40
STRESS_HIGH_THRESHOLD = 6
LATE_CAFFEINE_HOUR = 15


def _parse_hour(time_str: Optional[str]) -> Optional[int]:
    if not time_str:
        return None
    try:
        return int(time_str.split(":")[0])
    except (ValueError, IndexError):
        return None


def summarize_day(day: Dict) -> Dict:
    """Produce a structured summary of key indicators from a day's data."""
    summary: Dict[str, object] = {}
    fitbit = day.get("fitbit", {})
    manual = day.get("manual", {})

    sleep_hours = fitbit.get("sleep_hours")
    summary["sleep_short"] = bool(sleep_hours is not None and sleep_hours < SLEEP_SHORT_THRESHOLD)

    hrv = fitbit.get("hrv")
    summary["hrv_low"] = bool(hrv is not None and hrv < HRV_LOW_THRESHOLD)

    stress = manual.get("stress")
    summary["stress_high"] = bool(stress is not None and stress > STRESS_HIGH_THRESHOLD)

    anxiety = manual.get("anxiety")
    summary["anxiety_high"] = bool(anxiety is not None and anxiety > STRESS_HIGH_THRESHOLD)

    caffeine_time = manual.get("caffeine_time")
    hour = _parse_hour(caffeine_time)
    summary["late_caffeine"] = bool(hour is not None and hour >= LATE_CAFFEINE_HOUR)

    flags_true = [val for val in summary.values() if isinstance(val, bool) and val]
    summary["score"] = len(flags_true) / max(len(summary), 1)
    return summary


__all__ = ["summarize_day"]
