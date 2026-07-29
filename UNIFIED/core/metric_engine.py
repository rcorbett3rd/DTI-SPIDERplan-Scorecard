"""Configuration-driven metric scoring shared by all treatment sites."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from sites.base import MetricDefinition

from .homogeneity import score_homogeneity_index as _score_homogeneity_index


@dataclass(frozen=True)
class MetricEvaluation:
    value: float | None
    score: float
    status: str
    note: str


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def interpolate(
    value: float,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> float:
    if x0 == x1:
        return min(y0, y1)
    fraction = max(0.0, min(1.0, (value - x0) / (x1 - x0)))
    return y0 + fraction * (y1 - y0)


def status_from_score(score: float) -> str:
    if score >= 90.0:
        return "Achieved"
    if score >= 50.0:
        return "Marginal"
    return "Failed"


def score_lower_is_better(
    value: Any,
    *,
    preferred: float,
    acceptable: float | None = None,
    ideal: float | None = None,
    profile: str = "head_neck",
) -> MetricEvaluation:
    """Score a maximum-dose, mean-dose, or volume upper limit."""

    measured = finite_float(value)
    if measured is None:
        return MetricEvaluation(None, 0.0, "Unavailable", "Metric value unavailable.")

    preferred = float(preferred)
    acceptable = None if acceptable is None else float(acceptable)

    if profile == "prostate":
        ideal_value = float(ideal) if ideal is not None else 0.8 * preferred
        if measured <= ideal_value:
            score = 100.0
        elif measured <= preferred:
            score = interpolate(measured, ideal_value, 100.0, preferred, 75.0)
        else:
            score = 0.0
    else:
        if acceptable is None or acceptable <= preferred:
            ideal_value = float(ideal) if ideal is not None else 0.8 * preferred
            if measured <= ideal_value:
                score = 100.0
            elif measured <= preferred:
                score = interpolate(measured, ideal_value, 100.0, preferred, 90.0)
            else:
                score = 0.0
        else:
            if measured < preferred:
                score = 100.0
            elif measured <= acceptable:
                score = interpolate(measured, preferred, 90.0, acceptable, 50.0)
            else:
                score = 0.0

    rounded = round(score, 1)
    return MetricEvaluation(
        measured,
        rounded,
        status_from_score(rounded),
        f"{measured:g} evaluated against preferred {preferred:g}"
        + (
            f" and acceptable {acceptable:g}."
            if acceptable is not None
            else "."
        ),
    )


def score_v105(value: Any) -> MetricEvaluation:
    measured = finite_float(value)
    if measured is None:
        return MetricEvaluation(None, 0.0, "Unavailable", "V105% unavailable.")
    if measured <= 5.0:
        score = 100.0
    elif measured < 10.0:
        score = interpolate(measured, 5.0, 100.0, 10.0, 90.0)
    elif measured < 20.0:
        score = interpolate(measured, 10.0, 90.0, 20.0, 50.0)
    else:
        score = 0.0
    rounded = round(score, 1)
    return MetricEvaluation(
        measured,
        rounded,
        status_from_score(rounded),
        "V105% scored using the 5% / 10% / 20% ladder.",
    )


def score_target_coverage(v100: Any, v95: Any) -> MetricEvaluation:
    v100_value = finite_float(v100)
    v95_value = finite_float(v95)
    if v100_value is None or v95_value is None:
        return MetricEvaluation(None, 0.0, "Unavailable", "Coverage values unavailable.")

    if v100_value >= 100.0:
        score = 100.0
    elif v100_value >= 95.0:
        score = interpolate(v100_value, 95.0, 90.0, 100.0, 99.0)
    elif v95_value >= 95.0:
        score = interpolate(max(0.0, v100_value), 0.0, 70.0, 95.0, 90.0)
    else:
        score = 0.0

    rounded = round(score, 1)
    return MetricEvaluation(
        v100_value,
        rounded,
        status_from_score(rounded),
        f"V100Rx={v100_value:.1f}%; V95Rx={v95_value:.1f}%.",
    )


def score_target_minimum(
    percent_rx: Any,
    *,
    minimum: float = 80.0,
) -> MetricEvaluation:
    measured = finite_float(percent_rx)
    if measured is None:
        return MetricEvaluation(None, 0.0, "Unavailable", "Minimum dose unavailable.")
    score = 100.0 if measured >= minimum else 0.0
    return MetricEvaluation(
        measured,
        score,
        status_from_score(score),
        f"Dmin={measured:.1f}%Rx; minimum acceptable is {minimum:.1f}%Rx.",
    )



def score_homogeneity_index(value: Any) -> MetricEvaluation:
    """Score ICRU 83 HI using the approved 0.10 / 0.15 / 0.20 ladder."""
    evaluation = _score_homogeneity_index(value)
    return MetricEvaluation(
        evaluation.value,
        evaluation.score,
        evaluation.status,
        evaluation.note,
    )

def evaluate_definition(
    definition: MetricDefinition,
    metric_values: Mapping[str, Any],
    *,
    profile: str,
) -> MetricEvaluation:
    """Evaluate one configured metric definition from a metric-value mapping."""

    value = metric_values.get(definition.metric_type)
    return score_lower_is_better(
        value,
        preferred=(
            definition.preferred
            if definition.preferred is not None
            else definition.limit
        ),
        acceptable=definition.acceptable,
        ideal=definition.ideal,
        profile=profile,
    )
