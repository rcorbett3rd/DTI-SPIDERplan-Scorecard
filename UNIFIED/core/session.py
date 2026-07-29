"""Centralized Streamlit session-state initialization."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import streamlit as st

from .constants import DEFAULT_SITE


DEFAULT_SESSION: dict[str, Any] = {
    "site": DEFAULT_SITE,
    "plan_a": None,
    "plan_b": None,
    "plan_a_result": None,
    "plan_b_result": None,
    "score_inclusion": {},
    "oar_assignments": {},
    "prescription_assignments": {},
    "comparison": None,
    "processing_issues": [],
}


def initialize_session() -> None:
    """Initialize known state keys without overwriting active user data."""

    for key, value in DEFAULT_SESSION.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)


def reset_plan_state(plan_key: str) -> None:
    """Clear one plan slot while preserving treatment-site selection."""

    if plan_key not in {"plan_a", "plan_b"}:
        raise ValueError("plan_key must be 'plan_a' or 'plan_b'.")

    st.session_state[plan_key] = None
    st.session_state[f"{plan_key}_result"] = None


def clear_analysis_state() -> None:
    """Clear plan-dependent state when the selected treatment site changes."""

    preserved_site = st.session_state.get("site", DEFAULT_SITE)
    for key, value in DEFAULT_SESSION.items():
        st.session_state[key] = deepcopy(value)
    st.session_state["site"] = preserved_site
