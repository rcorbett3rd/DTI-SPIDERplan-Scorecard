"""Consistent section headings used by the shared Prostate-style interface."""

from __future__ import annotations

import streamlit as st


def section(title: str, caption: str | None = None) -> None:
    st.markdown(f"## {title}")
    if caption:
        st.caption(caption)


def subsection(title: str, caption: str | None = None) -> None:
    st.markdown(f"### {title}")
    if caption:
        st.caption(caption)


def empty_state(message: str) -> None:
    with st.container(border=True):
        st.info(message)
