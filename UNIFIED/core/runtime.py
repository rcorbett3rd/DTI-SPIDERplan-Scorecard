"""Shared runtime orchestration for single-plan and comparison workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .comparison_engine import ComparisonSummary, compare_results
from .release_validation import ValidationItem, validate_plan_result
from .score_pipeline import ScorePipelineOptions, process_scored_result


@dataclass
class PreparedPlan:
    result: dict[str, Any]
    validation: list[ValidationItem]
    available_structures: list[str]
    default_assignments: dict[str, str]


def prepare_plan(
    raw_result: Mapping[str, Any],
    *,
    display_name: str,
    treatment_site: str,
    oar_assignments: Mapping[str, str] | None = None,
    included_structures: set[str] | None = None,
    grade_function: Callable[[float], str] | None = None,
    treatability_function: Callable[[float], str] | None = None,
) -> PreparedPlan:
    pipeline = process_scored_result(
        raw_result,
        options=ScorePipelineOptions(
            display_name=display_name,
            treatment_site=treatment_site,
            oar_assignments=oar_assignments,
            included_structures=included_structures,
        ),
        grade_function=grade_function,
        treatability_function=treatability_function,
    )

    return PreparedPlan(
        result=pipeline.result,
        validation=validate_plan_result(pipeline.result),
        available_structures=pipeline.available_structures,
        default_assignments=pipeline.default_assignments,
    )


def prepare_comparison(
    plan_a: PreparedPlan | Mapping[str, Any],
    plan_b: PreparedPlan | Mapping[str, Any],
) -> ComparisonSummary:
    result_a = plan_a.result if isinstance(plan_a, PreparedPlan) else plan_a
    result_b = plan_b.result if isinstance(plan_b, PreparedPlan) else plan_b
    return compare_results(result_a, result_b)
