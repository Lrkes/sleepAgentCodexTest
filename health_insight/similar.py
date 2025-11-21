from __future__ import annotations

from typing import Dict, List

from .storage import get_all_days, get_day_json
from .summary import summarize_day


def _matching_flags(target_summary: Dict, comparison_summary: Dict) -> int:
    matches = 0
    for key, val in target_summary.items():
        if isinstance(val, bool) and val is True and comparison_summary.get(key) is True:
            matches += 1
    return matches


def find_similar_days(date_str: str, top_n: int = 5) -> List[Dict]:
    """Find past days that share similar summary flags with the target date."""
    target = get_day_json(date_str)
    if not target:
        return []
    target_summary = summarize_day(target)
    similar_days: List[Dict] = []
    for day in get_all_days():
        if day.get("date") == date_str:
            continue
        comparison_summary = summarize_day(day)
        score = _matching_flags(target_summary, comparison_summary)
        if score > 0:
            day_with_score = dict(day)
            day_with_score["similarity_score"] = score
            similar_days.append(day_with_score)
    similar_days.sort(key=lambda item: item.get("similarity_score", 0), reverse=True)
    return similar_days[:top_n]


__all__ = ["find_similar_days"]
