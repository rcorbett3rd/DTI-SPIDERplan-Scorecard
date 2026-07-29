"""Unified clinical evaluation pipeline.

DICOM and DVH sampling remain in the validated engines. This pipeline accepts
sampled structure metrics, applies site rules, assigns prescriptions, evaluates
configured metrics, and emits the shared result contract used by the Prostate
interface.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Mapping

from sites.registry import get_site

from .metric_engine import (
    evaluate_definition,
    score_target_coverage,
    score_target_minimum,
    score_v105,
)
from .prescription_engine import (
    assign_target_prescriptions,
    highest_assigned_dose,
)
from .result_contract import normalize_result, safe_mean


def _metric_row(
    *,
    structure: str,
    metric: str,
    value: Any,
    goal: str,
    score: float,
    domain: str,
    category: str,
    status: str,
    note: str,
    **extra: Any,
) -> dict[str, Any]:
    row = {
        "Structure": structure,
        "Metric": metric,
        "Value": value,
        "Goal": goal,
        "Score": score,
        "Domain": domain,
        "Category": category,
        "Status": status,
        "Notes": note,
    }
    row.update(extra)
    return row


def evaluate_case(
    *,
    treatment_site: str,
    structures: Mapping[str, Mapping[str, Any]],
    plan_prescription_gy: float | None = None,
    plan_metrics: Mapping[str, Any] | None = None,
    display_name: str = "Plan",
) -> dict[str, Any]:
    """Evaluate already sampled structure metrics through one clinical API.

    `structures` maps structure names to values such as:
    `V100Rx_%`, `V95Rx_%`, `V105Rx_%`, `Dmin_%Rx`, `Dmean_Gy`,
    `D0.03cc_Gy`, `V30Gy_%`, and `D5_Gy`.
    """

    site = get_site(treatment_site)
    profile = site.PROFILE

    assignments = assign_target_prescriptions(
        structures.keys(),
        is_target=site.is_target,
        is_eval_target=site.is_eval_target,
        semantic_doses=profile.standard_prescriptions_gy,
        plan_prescription_gy=plan_prescription_gy,
        eval_suffix=profile.eval_suffix,
    )
    assignment_map = {item.structure: item for item in assignments}
    highest_rx = highest_assigned_dose(assignments)

    rows: list[dict[str, Any]] = []
    domain_scores: dict[str, list[float]] = {}
    missing_eval_details: list[str] = []
    oar_candidates: dict[str, list[str]] = {}

    for structure_name, values in structures.items():
        if site.is_target(structure_name):
            assignment = assignment_map.get(structure_name)
            assigned_rx = assignment.prescription_gy if assignment else None

            if site.is_eval_target(structure_name):
                evaluation = score_v105(values.get("V105Rx_%"))
                rows.append(
                    _metric_row(
                        structure=structure_name,
                        metric="V105Rx_%",
                        value=values.get("V105Rx_%"),
                        goal="≤5% ideal; ≤10% preferred; <20% review",
                        score=evaluation.score,
                        domain="Target Dose Quality",
                        category="TV",
                        status=evaluation.status,
                        note=evaluation.note,
                        assigned_rx_gy=assigned_rx,
                    )
                )
                domain_scores.setdefault("Target Dose Quality", []).append(
                    evaluation.score
                )
                continue

            coverage = score_target_coverage(
                values.get("V100Rx_%"),
                values.get("V95Rx_%"),
            )
            minimum = score_target_minimum(values.get("Dmin_%Rx"), minimum=80.0)
            combined = min(coverage.score, minimum.score)

            rows.append(
                _metric_row(
                    structure=structure_name,
                    metric="Coverage",
                    value=values.get("V100Rx_%"),
                    goal="V100Rx/V95Rx coverage ladder",
                    score=combined,
                    domain="Target Coverage",
                    category="TV",
                    status="Achieved" if combined >= 90 else "Marginal" if combined >= 50 else "Failed",
                    note=f"{coverage.note} {minimum.note}",
                    assigned_rx_gy=assigned_rx,
                )
            )
            domain_scores.setdefault("Target Coverage", []).append(combined)

            # Highest-dose target may be evaluated directly. Lower-dose target
            # V105 belongs only on the matching eval target.
            if assigned_rx is not None and highest_rx is not None:
                if abs(assigned_rx - highest_rx) < 0.05:
                    hotspot = score_v105(values.get("V105Rx_%"))
                    rows.append(
                        _metric_row(
                            structure=structure_name,
                            metric="V105Rx_%",
                            value=values.get("V105Rx_%"),
                            goal="≤5% ideal; ≤10% preferred; <20% review",
                            score=hotspot.score,
                            domain="Target Dose Quality",
                            category="TV",
                            status=hotspot.status,
                            note="Highest-dose target evaluated directly.",
                            assigned_rx_gy=assigned_rx,
                        )
                    )
                    domain_scores.setdefault("Target Dose Quality", []).append(
                        hotspot.score
                    )
                else:
                    expected_eval = any(
                        site.is_eval_target(other_name)
                        and assignment_map.get(other_name) is not None
                        and assignment_map[other_name].prescription_gy is not None
                        and abs(
                            assignment_map[other_name].prescription_gy - assigned_rx
                        ) < 0.05
                        for other_name in structures
                    )
                    if not expected_eval:
                        missing_eval_details.append(
                            f"{structure_name}: matching eval target not found"
                        )
            continue

        canonical = site.canonical_oar_name(structure_name)
        if canonical is None:
            continue

        oar_candidates.setdefault(canonical, []).append(structure_name)
        definitions = site.configured_metrics_for(structure_name)
        for definition in definitions:
            evaluation = evaluate_definition(
                definition,
                values,
                profile=profile.key,
            )
            domain = canonical
            rows.append(
                _metric_row(
                    structure=structure_name,
                    metric=definition.metric_type,
                    value=evaluation.value,
                    goal=definition.label or f"≤{definition.limit:g}",
                    score=evaluation.score,
                    domain=domain,
                    category="OAR",
                    status=evaluation.status,
                    note=evaluation.note,
                    oar_group=canonical,
                )
            )
            domain_scores.setdefault(domain, []).append(evaluation.score)

    if plan_metrics:
        for metric_name, value in plan_metrics.items():
            rows.append(
                _metric_row(
                    structure="Plan",
                    metric=str(metric_name),
                    value=value,
                    goal="Plan-level review",
                    score=float(value) if isinstance(value, (int, float)) else 0.0,
                    domain="Plan Quality",
                    category="Plan",
                    status="Achieved",
                    note="Plan-level metric supplied by the active plan engine.",
                )
            )
            if isinstance(value, (int, float)):
                domain_scores.setdefault("Plan Quality", []).append(float(value))

    domains = {
        domain: safe_mean(scores)
        for domain, scores in domain_scores.items()
        if scores
    }
    overall = safe_mean(domains.values())

    raw_result = {
        "display_name": display_name,
        "treatment_site": profile.display_name,
        "metrics": rows,
        "domains": domains,
        "overall": overall,
        "grade": "",
        "treatability": (
            "Treatable"
            if overall >= 75
            else "Marginally Treatable"
            if overall >= 60
            else "Non-Treatable / REPLAN"
        ),
        "dvhs": {},
        "warnings": [],
        "structures": list(structures),
        "target_assignments": [asdict(item) for item in assignments],
        "oar_candidates": oar_candidates,
        "missing_eval": bool(missing_eval_details),
        "missing_eval_details": missing_eval_details,
    }
    return normalize_result(raw_result)
