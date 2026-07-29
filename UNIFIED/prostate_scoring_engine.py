from __future__ import annotations

import math
from typing import Any


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def lower_is_better(value: float, preferred: float, limit: float) -> float:
    if math.isnan(value):
        return math.nan
    if value <= preferred:
        return 100.0
    if value <= limit:
        return 100.0 - 25.0 * (value - preferred) / max(limit - preferred, 1e-9)
    return 0.0


def oar_score(value: float, limit: float) -> float:
    # Preferred at <=80% of limit; acceptable scales to 75 at the limit; over limit fails.
    return lower_is_better(value, 0.8 * limit, limit)


def coverage_score(v100: float, preferred: float = 98.0, minimum: float = 95.0) -> float:
    if math.isnan(v100):
        return math.nan
    if v100 >= preferred:
        return 100.0
    if v100 >= minimum:
        return 75.0 + 15.0 * (v100 - minimum) / max(preferred - minimum, 1e-9)
    return 0.0


def min_dose_score(percent_rx: float, preferred: float = 95.0, minimum: float = 93.0) -> float:
    if math.isnan(percent_rx):
        return math.nan
    if percent_rx >= preferred:
        return 100.0
    if percent_rx >= minimum:
        return 75.0 + 15.0 * (percent_rx - minimum) / max(preferred - minimum, 1e-9)
    return 0.0


def hotspot_score(percent_rx: float, preferred: float = 107.0, maximum: float = 110.0) -> float:
    if math.isnan(percent_rx):
        return math.nan
    if percent_rx <= preferred:
        return 100.0
    if percent_rx <= maximum:
        return 100.0 - 25.0 * (percent_rx - preferred) / max(maximum - preferred, 1e-9)
    return 0.0


def v105_score(value: float, ideal: float = 5.0, acceptable: float = 10.0) -> float:
    return lower_is_better(value, ideal, acceptable)


def muf_score(muf: float | None) -> float:
    if muf is None or math.isnan(muf):
        return math.nan
    if muf <= 3.0:
        return 100.0
    if muf <= 4.0:
        return 100.0 - 10.0 * (muf - 3.0)
    if muf <= 5.0:
        return 90.0 - 15.0 * (muf - 4.0)
    return 0.0


def grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def treatability(score: float) -> str:
    if score >= 75:
        return "Treatable"
    if score >= 60:
        return "Marginally Treatable"
    return "Non-Treatable / REPLAN"


def safe_mean(values: list[float]) -> float:
    good = [x for x in values if x is not None and not math.isnan(x)]
    return sum(good) / len(good) if good else math.nan
