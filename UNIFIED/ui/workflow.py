"""Reusable score-inclusion and OAR-assignment controls.

These controls mirror the finalized Prostate workflow and work with either
treatment site's normalized result.
"""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from core.assignment_engine import default_oar_assignments, scored_structures
from core.result_contract import normalize_result


def render_oar_assignment_controls(
    result: Mapping[str, Any],
    *,
    key_prefix: str,
) -> dict[str, str]:
    """Render one selector per configured OAR group."""

    normalized = normalize_result(result)
    candidates = normalized.get("oar_candidates", {})
    defaults = default_oar_assignments(normalized)
    assignments: dict[str, str] = {}

    if not candidates:
        st.caption("No OAR assignment choices were detected.")
        return assignments

    for group, available in candidates.items():
        options = [str(value) for value in available]
        if not options:
            continue

        default = defaults.get(str(group), options[0])
        default_index = options.index(default) if default in options else 0

        assignments[str(group)] = st.selectbox(
            str(group),
            options=options,
            index=default_index,
            key=f"{key_prefix}_oar_{group}",
        )

    return assignments


def render_score_inclusion_controls(
    result: Mapping[str, Any],
    *,
    key_prefix: str,
    default_included: bool = True,
) -> set[str]:
    """Render the structure checklist used by the finalized Prostate app."""

    structures = scored_structures(result)
    included: set[str] = set()

    if not structures:
        st.caption("No scored structures were detected.")
        return included

    columns = st.columns(3)
    for index, structure in enumerate(structures):
        with columns[index % len(columns)]:
            checked = st.checkbox(
                structure,
                value=default_included,
                key=f"{key_prefix}_include_{structure}",
            )
        if checked:
            included.add(structure)

    return included


def render_missing_eval_notice(result: Mapping[str, Any]) -> None:
    """Render the established blue missing-evaluation-structure notice."""

    normalized = normalize_result(result)
    if not normalized.get("missing_eval"):
        return

    details = normalized.get("missing_eval_details", [])
    detail_text = ", ".join(str(value) for value in details) if details else ""
    message = "Required evaluation target structure is missing."
    if detail_text:
        message += f" {detail_text}"

    st.info(message, icon="ℹ️")
