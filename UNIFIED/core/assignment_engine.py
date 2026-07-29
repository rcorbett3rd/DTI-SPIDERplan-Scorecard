"""Shared OAR assignment and score-inclusion logic.

This is extracted from the matching implementations in `prostate_site.py` and
`head_neck_site.py`. It operates on the unified result contract and contains no
disease-specific scoring thresholds.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable, Mapping

from sites.common import normalize_structure_name

from .result_contract import finite_number, normalize_result, safe_mean


GradeFunction = Callable[[float], str]
TreatabilityFunction = Callable[[float], str]


def default_oar_candidate(group: str, candidates: Iterable[str]) -> str:
    """Prefer the base OAR contour over derived OAR-minus-target contours."""

    available = [str(candidate) for candidate in candidates if str(candidate)]
    if not available:
        return ""

    group_normalized = normalize_structure_name(group)
    exact = [
        name
        for name in available
        if normalize_structure_name(name) == group_normalized
    ]
    if exact:
        return exact[0]

    target_tokens = ("ptv", "ctv", "gtv", "itv", "tv")
    non_target_derived = [
        name
        for name in available
        if not any(token in name.lower() for token in target_tokens)
    ]
    pool = non_target_derived or available
    return sorted(pool, key=lambda value: (len(value), value.lower()))[0]


def default_oar_assignments(
    result: Mapping[str, Any],
) -> dict[str, str]:
    """Create initial assignments from a result's OAR candidate map."""

    normalized = normalize_result(result)
    return {
        str(group): default_oar_candidate(str(group), candidates)
        for group, candidates in normalized.get("oar_candidates", {}).items()
        if candidates
    }


def apply_oar_assignments(
    result: Mapping[str, Any],
    assignments: Mapping[str, str],
) -> dict[str, Any]:
    """Keep only the selected structure for each configured OAR group."""

    filtered = normalize_result(result)
    kept_rows: list[dict[str, Any]] = []

    for row in filtered["metrics"]:
        if row.get("category") != "OAR":
            kept_rows.append(row)
            continue

        group = row.get("oar_group")
        selected = assignments.get(group)
        if selected is None or row.get("structure") == selected:
            kept_rows.append(row)

    filtered["metrics"] = kept_rows
    filtered["oar_assignments"] = dict(assignments)
    return filtered


def scored_structures(result: Mapping[str, Any]) -> list[str]:
    """Return unique structures that may be checked on or off from scoring."""

    normalized = normalize_result(result)
    values = {
        str(row.get("structure", ""))
        for row in normalized["metrics"]
        if row.get("structure") and row.get("structure") != "Plan"
    }
    return sorted(values, key=str.lower)


def apply_score_inclusions(
    result: Mapping[str, Any],
    included_structures: Iterable[str],
    *,
    grade_function: GradeFunction | None = None,
    treatability_function: TreatabilityFunction | None = None,
) -> dict[str, Any]:
    """Filter metrics and recompute domains and overall score.

    Site-specific grade and treatability callbacks may be passed to preserve the
    current engines' exact display labels.
    """

    filtered = normalize_result(result)
    included = {str(value) for value in included_structures}

    rows = [
        row
        for row in filtered["metrics"]
        if row.get("structure") == "Plan"
        or row.get("structure") in included
    ]

    domains: dict[str, list[float]] = {}
    for row in rows:
        score = finite_number(row.get("score"))
        if score is None:
            continue
        domains.setdefault(str(row.get("domain", "Other")), []).append(score)

    filtered["metrics"] = rows
    filtered["domains"] = {
        domain: safe_mean(scores)
        for domain, scores in domains.items()
        if scores
    }
    filtered["overall"] = safe_mean(filtered["domains"].values())

    if grade_function is not None:
        filtered["grade"] = grade_function(filtered["overall"])
    if treatability_function is not None:
        filtered["treatability"] = treatability_function(filtered["overall"])

    return filtered
