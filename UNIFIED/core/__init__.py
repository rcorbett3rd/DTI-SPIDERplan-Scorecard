"""Shared infrastructure for the DTI SPIDERplan Scorecard."""

from .clinical_pipeline import evaluate_case
from .comparison_engine import ComparisonSummary, compare_results
from .constants import APP_NAME, DEFAULT_SITE, SUPPORTED_SITES, VERSION
from .models import PlanIdentity, ProcessingIssue, ProcessingResult
from .runtime import PreparedPlan, prepare_comparison, prepare_plan
from .score_pipeline import (
    ScorePipelineOptions,
    ScorePipelineOutput,
    process_scored_result,
)

__all__ = [
    "APP_NAME",
    "DEFAULT_SITE",
    "SUPPORTED_SITES",
    "VERSION",
    "PlanIdentity",
    "ProcessingIssue",
    "ProcessingResult",
    "ScorePipelineOptions",
    "ScorePipelineOutput",
    "process_scored_result",
    "evaluate_case",
    "ComparisonSummary",
    "compare_results",
    "PreparedPlan",
    "prepare_plan",
    "prepare_comparison",
]
