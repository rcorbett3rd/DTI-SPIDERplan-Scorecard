"""Shared ICRU 83 target homogeneity calculations and scoring.

HI = (D2% - D98%) / D50%

The ratio is dimensionless, so equivalent Gy or %Rx dose values may be used
as long as D2, D50, and D98 use the same units.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


HI_DISPLAY_NAME = "Homogeneity Index (ICRU)"
HI_GOAL = "≤0.10 ideal; 0.10–0.15 preferred; 0.15–0.20 review"
HI_TOOLTIP = (
    "Homogeneity Index (ICRU): Measures dose uniformity within the target using "
    "HI = (D2% − D98%) / D50%. Lower values indicate a more homogeneous dose "
    "distribution. This complements the existing V95%, V100%, V105%, and hotspot "
    "metrics by evaluating overall internal dose uniformity."
)


@dataclass(frozen=True)
class HomogeneityEvaluation:
    value: float | None
    score: float
    status: str
    note: str


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _interpolate(value: float, x0: float, y0: float, x1: float, y1: float) -> float:
    if x0 == x1:
        return min(y0, y1)
    fraction = max(0.0, min(1.0, (value - x0) / (x1 - x0)))
    return y0 + fraction * (y1 - y0)


def homogeneity_index(d2: Any, d50: Any, d98: Any) -> float | None:
    """Return ICRU 83 HI from consistently-unitized D2, D50, and D98 values."""
    d2_value = _finite(d2)
    d50_value = _finite(d50)
    d98_value = _finite(d98)
    if d2_value is None or d50_value is None or d98_value is None or d50_value <= 0:
        return None
    return max(0.0, (d2_value - d98_value) / d50_value)


def score_homogeneity_index(value: Any) -> HomogeneityEvaluation:
    """Score HI using the approved 0.10 / 0.15 / 0.20 ladder."""
    measured = _finite(value)
    if measured is None:
        return HomogeneityEvaluation(None, 0.0, "Unavailable", "HI unavailable.")
    if measured <= 0.10:
        score = 100.0
    elif measured <= 0.15:
        score = _interpolate(measured, 0.10, 100.0, 0.15, 90.0)
    elif measured <= 0.20:
        score = _interpolate(measured, 0.15, 90.0, 0.20, 50.0)
    else:
        score = 0.0
    rounded = round(score, 1)
    status = "Achieved" if rounded >= 90 else "Marginal" if rounded >= 50 else "Failed"
    return HomogeneityEvaluation(
        measured,
        rounded,
        status,
        f"HI={measured:.3f}; lower values indicate more homogeneous target dose.",
    )


def should_score_target_homogeneity(
    structure_name: str,
    assigned_rx_gy: Any,
    highest_rx_gy: Any,
    *,
    eval_suffix: str = "_eval",
) -> bool:
    """Apply the approved SIB rule: highest PTV or lower-dose matching PTV_eval."""
    normalized = str(structure_name).strip().lower()
    if "ptv" not in normalized or normalized.endswith("opti"):
        return False
    if normalized.endswith(eval_suffix.lower()) or "eval" in normalized:
        return True
    assigned = _finite(assigned_rx_gy)
    highest = _finite(highest_rx_gy)
    return assigned is not None and highest is not None and math.isclose(
        assigned, highest, abs_tol=0.05
    )


def format_homogeneity_details(d2: Any, d50: Any, d98: Any, hi: Any) -> str:
    values = [_finite(d2), _finite(d50), _finite(d98), _finite(hi)]
    if any(value is None for value in values):
        return "HI unavailable"
    d2v, d50v, d98v, hiv = values
    return f"D2={d2v:.2f} Gy; D50={d50v:.2f} Gy; D98={d98v:.2f} Gy; HI={hiv:.3f}"
