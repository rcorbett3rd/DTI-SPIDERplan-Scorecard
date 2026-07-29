"""Shared CSV, JSON, and PDF-ready export preparation."""

from __future__ import annotations

from dataclasses import asdict
from io import BytesIO
import json
from typing import Any, Mapping

import pandas as pd

from .comparison_engine import ComparisonSummary
from .result_contract import normalize_result


def result_export_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    normalized = normalize_result(result)
    return {
        "display_name": normalized.get("display_name"),
        "treatment_site": normalized.get("treatment_site"),
        "overall": normalized.get("overall"),
        "grade": normalized.get("grade"),
        "treatability": normalized.get("treatability"),
        "domains": normalized.get("domains", {}),
        "metrics": normalized.get("metrics", []),
        "warnings": normalized.get("warnings", []),
        "missing_eval": normalized.get("missing_eval", False),
        "missing_eval_details": normalized.get("missing_eval_details", []),
        "target_assignments": normalized.get("target_assignments", {}),
        "oar_assignments": normalized.get("oar_assignments", {}),
        "plan_summary": normalized.get("plan_summary", {}),
    }


def result_json_bytes(result: Mapping[str, Any]) -> bytes:
    return json.dumps(
        result_export_payload(result),
        indent=2,
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def result_csv_bytes(result: Mapping[str, Any]) -> bytes:
    normalized = normalize_result(result)
    return pd.DataFrame(normalized["metrics"]).to_csv(index=False).encode("utf-8")


def comparison_json_bytes(summary: ComparisonSummary) -> bytes:
    return json.dumps(
        asdict(summary),
        indent=2,
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def comparison_csv_bytes(summary: ComparisonSummary) -> bytes:
    return pd.DataFrame(summary.metric_rows).to_csv(index=False).encode("utf-8")


def report_context(
    result: Mapping[str, Any],
    *,
    application_name: str,
    legal_notice: str,
) -> dict[str, Any]:
    """Return a stable context for the active PDF reporting implementation."""

    payload = result_export_payload(result)
    payload["application_name"] = application_name
    payload["legal_notice"] = legal_notice
    return payload


def safe_filename(value: str, suffix: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in str(value).strip()
    ).strip("_")
    return f"{cleaned or 'SPIDERplan'}{suffix}"
