"""Shared plan-comparison calculations.

This module compares normalized plan results without depending on Streamlit.
It supports the finalized overall, target-only, OAR-only, domain, metric, and
DVH comparison views.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

import pandas as pd

from .result_contract import finite_number, normalize_result


@dataclass(frozen=True)
class ComparisonSummary:
    plan_a_name: str
    plan_b_name: str
    plan_a_score: float
    plan_b_score: float
    difference: float
    winner: str
    target_a: float
    target_b: float
    oar_a: float
    oar_b: float
    domain_rows: list[dict[str, Any]] = field(default_factory=list)
    metric_rows: list[dict[str, Any]] = field(default_factory=list)


def _score(value: Any) -> float:
    number = finite_number(value)
    return float(number) if number is not None else 0.0


def _category_score(result: Mapping[str, Any], category: str) -> float:
    normalized = normalize_result(result)
    values = [
        _score(row.get("score"))
        for row in normalized["metrics"]
        if str(row.get("category", "")).upper() == category.upper()
        and finite_number(row.get("score")) is not None
    ]
    return sum(values) / len(values) if values else 0.0


def winner_label(score_a: Any, score_b: Any, tolerance: float = 1e-9) -> str:
    a = _score(score_a)
    b = _score(score_b)
    if abs(a - b) <= tolerance:
        return "Tie"
    return "Plan A" if a > b else "Plan B"


def compare_domains(
    result_a: Mapping[str, Any],
    result_b: Mapping[str, Any],
) -> list[dict[str, Any]]:
    a = normalize_result(result_a)
    b = normalize_result(result_b)
    domains = sorted(set(a["domains"]) | set(b["domains"]), key=str.lower)

    rows: list[dict[str, Any]] = []
    for domain in domains:
        score_a = _score(a["domains"].get(domain))
        score_b = _score(b["domains"].get(domain))
        rows.append(
            {
                "Domain": domain,
                "Plan A": round(score_a, 1),
                "Plan B": round(score_b, 1),
                "Difference": round(score_a - score_b, 1),
                "Better Plan": winner_label(score_a, score_b),
            }
        )
    return rows


def _metric_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("structure", "")),
        str(row.get("metric", "")),
        str(row.get("domain", "")),
    )


def compare_metrics(
    result_a: Mapping[str, Any],
    result_b: Mapping[str, Any],
) -> list[dict[str, Any]]:
    a = normalize_result(result_a)
    b = normalize_result(result_b)

    rows_a = {_metric_key(row): row for row in a["metrics"]}
    rows_b = {_metric_key(row): row for row in b["metrics"]}
    keys = sorted(set(rows_a) | set(rows_b), key=lambda item: tuple(v.lower() for v in item))

    compared: list[dict[str, Any]] = []
    for key in keys:
        row_a = rows_a.get(key, {})
        row_b = rows_b.get(key, {})
        score_a = _score(row_a.get("score")) if row_a else 0.0
        score_b = _score(row_b.get("score")) if row_b else 0.0

        compared.append(
            {
                "Structure": key[0],
                "Metric": key[1],
                "Domain": key[2],
                "Plan A Value": row_a.get("value"),
                "Plan B Value": row_b.get("value"),
                "Plan A Score": round(score_a, 1),
                "Plan B Score": round(score_b, 1),
                "Difference": round(score_a - score_b, 1),
                "Better Plan": winner_label(score_a, score_b),
            }
        )
    return compared


def compare_results(
    result_a: Mapping[str, Any],
    result_b: Mapping[str, Any],
) -> ComparisonSummary:
    a = normalize_result(result_a)
    b = normalize_result(result_b)

    score_a = _score(a.get("overall"))
    score_b = _score(b.get("overall"))

    return ComparisonSummary(
        plan_a_name=str(a.get("display_name", "Plan A")),
        plan_b_name=str(b.get("display_name", "Plan B")),
        plan_a_score=round(score_a, 1),
        plan_b_score=round(score_b, 1),
        difference=round(score_a - score_b, 1),
        winner=winner_label(score_a, score_b),
        target_a=round(_category_score(a, "TV"), 1),
        target_b=round(_category_score(b, "TV"), 1),
        oar_a=round(_category_score(a, "OAR"), 1),
        oar_b=round(_category_score(b, "OAR"), 1),
        domain_rows=compare_domains(a, b),
        metric_rows=compare_metrics(a, b),
    )


def comparison_dataframe(summary: ComparisonSummary) -> pd.DataFrame:
    return pd.DataFrame(summary.metric_rows)
