"""Shared display labels for scores and plan treatability."""

from __future__ import annotations

import math
from typing import Any


def finite_score(value: Any) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return score if math.isfinite(score) else None


def score_status(value: Any) -> str:
    """Return the current SPIDERplan metric status label."""

    score = finite_score(value)
    if score is None:
        return "Not scored"
    if score >= 90.0:
        return "Achieved"
    if score >= 75.0:
        return "Marginal"
    return "Failed"


def treatability_label(value: Any) -> str:
    """Return the established plan-level treatability classification."""

    score = finite_score(value)
    if score is None:
        return "Not scored"
    if score >= 75.0:
        return "Treatable"
    if score >= 60.0:
        return "Marginally Treatable"
    return "Non-Treatable / REPLAN"


def winner(score_a: Any, score_b: Any, tolerance: float = 1e-9) -> str | None:
    """Return Plan A, Plan B, Tie, or None."""

    a = finite_score(score_a)
    b = finite_score(score_b)
    if a is None and b is None:
        return None
    if a is None:
        return "Plan B"
    if b is None:
        return "Plan A"
    if abs(a - b) <= tolerance:
        return "Tie"
    return "Plan A" if a > b else "Plan B"
