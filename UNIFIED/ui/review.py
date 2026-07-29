"""Shared detailed-review and validation sections."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
import streamlit as st

from core.release_validation import ValidationItem
from core.result_contract import normalize_result
from .tables import style_metric_table


def render_validation_items(items: list[ValidationItem]) -> None:
    for item in items:
        if item.level == "error":
            st.error(item.message)
        elif item.level == "warning":
            st.warning(item.message)
        else:
            st.info(item.message)


def render_detailed_review(result: Mapping[str, Any]) -> None:
    normalized = normalize_result(result)
    frame = pd.DataFrame(normalized["metrics"])

    st.markdown("## Detailed Review")
    if frame.empty:
        st.info("No configured metrics are available.")
        return

    columns = [
        column
        for column in (
            "structure",
            "metric",
            "value",
            "goal",
            "score",
            "status",
            "domain",
        )
        if column in frame.columns
    ]
    st.dataframe(
        style_metric_table(frame[columns]),
        use_container_width=True,
        hide_index=True,
    )

    unconfigured = [
        name
        for name in normalized.get("structures", [])
        if name not in set(frame.get("structure", []))
    ]
    if unconfigured:
        with st.expander("Contours without configured scoring metrics"):
            st.caption(
                "These contours are retained for review but are not included "
                "in the score."
            )
            st.write(", ".join(sorted(map(str, unconfigured), key=str.lower)))
