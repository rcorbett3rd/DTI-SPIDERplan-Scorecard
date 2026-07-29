"""Head & Neck adapter for the shared clinical pipeline.

This module contains no legacy Head & Neck UI code.
"""

from __future__ import annotations

from typing import Any, Mapping

from core.clinical_pipeline import evaluate_case


def evaluate_sampled_metrics(
    structures: Mapping[str, Mapping[str, Any]],
    *,
    plan_prescription_gy: float | None = None,
    plan_metrics: Mapping[str, Any] | None = None,
    display_name: str = "Plan",
) -> dict[str, Any]:
    return evaluate_case(
        treatment_site="Head & Neck",
        structures=structures,
        plan_prescription_gy=plan_prescription_gy,
        plan_metrics=plan_metrics,
        display_name=display_name,
    )
