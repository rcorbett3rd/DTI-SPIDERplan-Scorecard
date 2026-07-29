"""Reusable Prostate-style interface components."""

from .comparison import render_comparison_dvh, render_comparison_summary
from .dvh import make_crosshair_dvh, make_comparison_crosshair_dvh
from .export_panel import render_comparison_exports, render_plan_exports
from .exports import csv_bytes, json_bytes
from .review import render_detailed_review, render_validation_items
from .status import score_status, treatability_label
from .tables import style_metric_table
from .workflow import (
    render_missing_eval_notice,
    render_oar_assignment_controls,
    render_score_inclusion_controls,
)

__all__ = [
    "make_crosshair_dvh",
    "make_comparison_crosshair_dvh",
    "render_comparison_dvh",
    "render_comparison_summary",
    "render_comparison_exports",
    "render_plan_exports",
    "render_detailed_review",
    "render_validation_items",
    "csv_bytes",
    "json_bytes",
    "score_status",
    "treatability_label",
    "style_metric_table",
    "render_missing_eval_notice",
    "render_oar_assignment_controls",
    "render_score_inclusion_controls",
]
