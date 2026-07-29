"""Shared download controls for single-plan and comparison results."""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from core.comparison_engine import ComparisonSummary
from core.export_engine import (
    comparison_csv_bytes,
    comparison_json_bytes,
    result_csv_bytes,
    result_json_bytes,
    safe_filename,
)


def render_plan_exports(result: Mapping[str, Any], *, key_prefix: str) -> None:
    name = str(result.get("display_name", "Plan"))
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "Download metric CSV",
            data=result_csv_bytes(result),
            file_name=safe_filename(name, "_metrics.csv"),
            mime="text/csv",
            key=f"{key_prefix}_csv",
            use_container_width=True,
        )

    with col2:
        st.download_button(
            "Download review JSON",
            data=result_json_bytes(result),
            file_name=safe_filename(name, "_review.json"),
            mime="application/json",
            key=f"{key_prefix}_json",
            use_container_width=True,
        )


def render_comparison_exports(
    summary: ComparisonSummary,
    *,
    key_prefix: str = "comparison",
) -> None:
    base_name = f"{summary.plan_a_name}_vs_{summary.plan_b_name}"
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "Download comparison CSV",
            data=comparison_csv_bytes(summary),
            file_name=safe_filename(base_name, "_comparison.csv"),
            mime="text/csv",
            key=f"{key_prefix}_csv",
            use_container_width=True,
        )

    with col2:
        st.download_button(
            "Download comparison JSON",
            data=comparison_json_bytes(summary),
            file_name=safe_filename(base_name, "_comparison.json"),
            mime="application/json",
            key=f"{key_prefix}_json",
            use_container_width=True,
        )
