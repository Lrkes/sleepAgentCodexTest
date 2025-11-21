from __future__ import annotations

import datetime as dt
from math import sqrt
from typing import Dict, Iterable, List, Optional, Tuple

from .storage import GLOBAL_PATTERNS_PATH, get_all_days
from .summary import summarize_day


def _average(values: Iterable[float]) -> Optional[float]:
    values_list = [v for v in values if v is not None]
    if not values_list:
        return None
    return sum(values_list) / len(values_list)


def _pearson_correlation(pairs: List[Tuple[float, float]]) -> Optional[float]:
    if len(pairs) < 2:
        return None
    xs, ys = zip(*pairs)
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denom_x = sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return None
    return numerator / (denom_x * denom_y)


def _extract_caffeine_sleep_pairs(history: List[Dict]) -> List[Tuple[float, float]]:
    pairs: List[Tuple[float, float]] = []
    for day in history:
        caffeine = day.get("manual", {}).get("caffeine_time")
        sleep = day.get("fitbit", {}).get("sleep_hours")
        if caffeine is None or sleep is None:
            continue
        try:
            hour, minute = caffeine.split(":")
            caffeine_hour = int(hour) + int(minute) / 60
        except (ValueError, IndexError):
            continue
        pairs.append((caffeine_hour, float(sleep)))
    return pairs


def _tough_day_triggers(history: List[Dict]) -> List[str]:
    summary_counts: Dict[str, int] = {}
    tough_days = [summarize_day(day) for day in history if summarize_day(day).get("stress_high")]
    if not tough_days:
        return []
    for summary in tough_days:
        for key, value in summary.items():
            if isinstance(value, bool) and value:
                summary_counts[key] = summary_counts.get(key, 0) + 1
    ranked = sorted(summary_counts.items(), key=lambda item: item[1], reverse=True)
    return [item[0] for item in ranked[:3]]


def compute_global_patterns() -> Dict:
    """Compute and persist global averages and correlations across all days."""
    history = get_all_days()
    sleep_values = [day.get("fitbit", {}).get("sleep_hours") for day in history]
    hrv_values = [day.get("fitbit", {}).get("hrv") for day in history]
    stress_values = [day.get("manual", {}).get("stress") for day in history]

    caffeine_sleep_pairs = _extract_caffeine_sleep_pairs(history)
    caffeine_sleep_corr = _pearson_correlation(caffeine_sleep_pairs)

    result: Dict[str, object] = {
        "last_computed": dt.date.today().isoformat(),
        "sleep_avg": _average([v for v in sleep_values if v is not None]),
        "hrv_avg": _average([v for v in hrv_values if v is not None]),
        "stress_avg": _average([v for v in stress_values if v is not None]),
        "caffeine_sleep_corr": round(caffeine_sleep_corr, 3) if caffeine_sleep_corr is not None else None,
        "stress_triggers": _tough_day_triggers(history),
    }

    GLOBAL_PATTERNS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GLOBAL_PATTERNS_PATH.open("w", encoding="utf-8") as f:
        import json

        json.dump(result, f, indent=2)
    return result


__all__ = ["compute_global_patterns"]
