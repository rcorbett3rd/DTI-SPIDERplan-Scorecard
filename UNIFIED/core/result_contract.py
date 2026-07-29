"""Unified result contract for both treatment sites.

The finalized Prostate interface expects a predictable dictionary shape.
This module normalizes existing Prostate and Head & Neck analysis results into
that shape without changing the underlying clinical calculations.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Iterable, Mapping

import pandas as pd


REQUIRED_RESULT_KEYS = (
    "metrics",
    "domains",
    "overall",
    "grade",
    "treatability",
    "dvhs",
)


def finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def safe_mean(values: Iterable[Any]) -> float:
    numbers = [
        number
        for value in values
        if (number := finite_number(value)) is not None
    ]
    return float(sum(numbers) / len(numbers)) if numbers else 0.0


def normalize_metric_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize capitalization differences between existing site engines."""

    normalized = dict(row)

    aliases = {
        "Structure": "structure",
        "Metric": "metric",
        "Value": "value",
        "Goal": "goal",
        "Score": "score",
        "Domain": "domain",
        "Category": "category",
        "Status": "status",
    }
    for source, destination in aliases.items():
        if destination not in normalized and source in normalized:
            normalized[destination] = normalized[source]

    normalized.setdefault("structure", "")
    normalized.setdefault("metric", "")
    normalized.setdefault("domain", "Other")
    normalized.setdefault("category", "Unconfigured")
    normalized.setdefault("score", None)
    return normalized


def normalize_result(
    result: Mapping[str, Any],
    *,
    display_name: str | None = None,
    treatment_site: str | None = None,
) -> dict[str, Any]:
    """Return a defensive, unified copy of a site analysis result."""

    normalized = deepcopy(dict(result))
    normalized["metrics"] = [
        normalize_metric_row(row)
        for row in normalized.get("metrics", [])
        if isinstance(row, Mapping)
    ]
    normalized["domains"] = {
        str(domain): float(score)
        for domain, score in dict(normalized.get("domains", {})).items()
        if finite_number(score) is not None
    }
    normalized.setdefault("dvhs", {})
    normalized.setdefault("warnings", [])
    normalized.setdefault("structures", [])
    normalized.setdefault("oar_candidates", {})
    normalized.setdefault("oar_assignments", {})
    normalized.setdefault("target_assignments", {})
    normalized.setdefault("missing_eval", False)
    normalized.setdefault("missing_eval_details", [])
    normalized.setdefault("plan_summary", {})

    if display_name is not None:
        normalized["display_name"] = display_name
    else:
        normalized.setdefault(
            "display_name",
            normalized.get("label", normalized.get("plan_name", "Plan")),
        )

    if treatment_site is not None:
        normalized["treatment_site"] = treatment_site

    if finite_number(normalized.get("overall")) is None:
        normalized["overall"] = safe_mean(normalized["domains"].values())

    normalized.setdefault("grade", "")
    normalized.setdefault("treatability", "")
    return normalized


def result_metrics_dataframe(result: Mapping[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(normalize_result(result)["metrics"])


def validate_result(result: Mapping[str, Any]) -> list[str]:
    """Return contract validation messages; an empty list means valid."""

    issues: list[str] = []
    for key in REQUIRED_RESULT_KEYS:
        if key not in result:
            issues.append(f"Missing result key: {key}")

    metrics = result.get("metrics", [])
    if not isinstance(metrics, list):
        issues.append("Result metrics must be a list.")

    domains = result.get("domains", {})
    if not isinstance(domains, Mapping):
        issues.append("Result domains must be a mapping.")

    dvhs = result.get("dvhs", {})
    if not isinstance(dvhs, Mapping):
        issues.append("Result DVHs must be a mapping.")

    return issues
