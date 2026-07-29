"""Shared Prostate-style comparison presentation."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.comparison_engine import ComparisonSummary, compare_results
from .cards import render_comparison_cards
from .dvh import make_comparison_crosshair_dvh


def _domain_figure(summary: ComparisonSummary) -> go.Figure:
    frame = pd.DataFrame(summary.domain_rows)
    figure = go.Figure()
    if not frame.empty:
        figure.add_trace(
            go.Scatterpolar(
                r=frame["Plan A"],
                theta=frame["Domain"],
                fill="toself",
                name=summary.plan_a_name,
            )
        )
        figure.add_trace(
            go.Scatterpolar(
                r=frame["Plan B"],
                theta=frame["Domain"],
                fill="toself",
                name=summary.plan_b_name,
            )
        )
    figure.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    return figure


def render_comparison_summary(
    result_a: Mapping[str, Any],
    result_b: Mapping[str, Any],
) -> ComparisonSummary:
    summary = compare_results(result_a, result_b)

    render_comparison_cards(
        summary.plan_a_score,
        summary.plan_b_score,
        label_a=summary.plan_a_name,
        label_b=summary.plan_b_name,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Target comparison",
            f"{summary.target_a:.1f} vs {summary.target_b:.1f}",
            f"{summary.target_a - summary.target_b:+.1f}",
        )
    with col2:
        st.metric(
            "OAR comparison",
            f"{summary.oar_a:.1f} vs {summary.oar_b:.1f}",
            f"{summary.oar_a - summary.oar_b:+.1f}",
        )

    st.plotly_chart(_domain_figure(summary), use_container_width=True)

    with st.expander("Detailed metric comparison", expanded=False):
        st.dataframe(
            pd.DataFrame(summary.metric_rows),
            use_container_width=True,
            hide_index=True,
        )

    return summary


def render_comparison_dvh(
    result_a: Mapping[str, Any],
    result_b: Mapping[str, Any],
) -> None:
    dvhs_a = result_a.get("dvhs", {})
    dvhs_b = result_b.get("dvhs", {})
    if not dvhs_a and not dvhs_b:
        st.info("No DVH curves are available for comparison.")
        return

    figure = make_comparison_crosshair_dvh(
        dvhs_a,
        dvhs_b,
        plan_a_name=str(result_a.get("display_name", "Plan A")),
        plan_b_name=str(result_b.get("display_name", "Plan B")),
    )
    st.plotly_chart(figure, use_container_width=True)
