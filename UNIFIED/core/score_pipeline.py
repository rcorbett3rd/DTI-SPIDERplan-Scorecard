"""Shared post-analysis scoring pipeline.

The site engines continue to calculate the clinical metrics. This pipeline
applies user OAR assignments, score-inclusion choices, result normalization,
and contract validation in one consistent order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping

from .assignment_engine import (
    apply_oar_assignments,
    apply_score_inclusions,
    default_oar_assignments,
    scored_structures,
)
from .result_contract import normalize_result, validate_result


@dataclass
class ScorePipelineOptions:
    display_name: str | None = None
    treatment_site: str | None = None
    oar_assignments: Mapping[str, str] | None = None
    included_structures: Iterable[str] | None = None


@dataclass
class ScorePipelineOutput:
    result: dict[str, Any]
    validation_issues: list[str] = field(default_factory=list)
    available_structures: list[str] = field(default_factory=list)
    default_assignments: dict[str, str] = field(default_factory=dict)


def process_scored_result(
    raw_result: Mapping[str, Any],
    *,
    options: ScorePipelineOptions | None = None,
    grade_function: Callable[[float], str] | None = None,
    treatability_function: Callable[[float], str] | None = None,
) -> ScorePipelineOutput:
    """Apply the shared result-processing workflow."""

    options = options or ScorePipelineOptions()
    result = normalize_result(
        raw_result,
        display_name=options.display_name,
        treatment_site=options.treatment_site,
    )

    assignments = (
        dict(options.oar_assignments)
        if options.oar_assignments is not None
        else default_oar_assignments(result)
    )
    result = apply_oar_assignments(result, assignments)

    structures = scored_structures(result)
    included = (
        set(options.included_structures)
        if options.included_structures is not None
        else set(structures)
    )
    result = apply_score_inclusions(
        result,
        included,
        grade_function=grade_function,
        treatability_function=treatability_function,
    )

    return ScorePipelineOutput(
        result=result,
        validation_issues=validate_result(result),
        available_structures=structures,
        default_assignments=assignments,
    )
