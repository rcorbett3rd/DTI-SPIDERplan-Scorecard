"""Shared sidebar controls."""

from __future__ import annotations

import streamlit as st

from core.constants import VERSION
from sites.registry import display_names


def treatment_site_selector(*, key: str = "unified_treatment_site") -> str:
    """Render the permanent treatment-site selector."""

    with st.sidebar:
        st.markdown("## DTI SPIDERplan")
        selected = st.selectbox(
            "Treatment site",
            options=display_names(),
            key=key,
        )
        st.caption(f"Version {VERSION}")
        st.divider()
    return selected
