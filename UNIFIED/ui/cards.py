"""Shared summary and comparison cards for Streamlit."""

from __future__ import annotations

from typing import Any

import streamlit as st

from .status import finite_score, treatability_label, winner


def render_plan_score_card(
    label: str,
    score: Any,
    *,
    selected_as_better: bool = False,
) -> None:
    """Render one finalized Prostate-style plan score card."""

    numeric = finite_score(score)
    displayed = "—" if numeric is None else f"{numeric:.1f}"
    badge = " ✅" if selected_as_better else ""

    with st.container(border=True):
        st.markdown(f"### {label}{badge}")
        st.metric("SPIDERplan score", displayed)
        st.caption(treatability_label(numeric))


def render_comparison_cards(
    score_a: Any,
    score_b: Any,
    *,
    label_a: str = "Plan A",
    label_b: str = "Plan B",
) -> str | None:
    """Render aligned Plan A/Plan B cards and return the winner."""

    better = winner(score_a, score_b)
    col_a, col_b = st.columns(2)

    with col_a:
        render_plan_score_card(
            label_a,
            score_a,
            selected_as_better=better == "Plan A",
        )
    with col_b:
        render_plan_score_card(
            label_b,
            score_b,
            selected_as_better=better == "Plan B",
        )

    if better == "Tie":
        st.info("The plans have the same overall SPIDERplan score.")
    return better
