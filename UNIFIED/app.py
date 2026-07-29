from __future__ import annotations

from pathlib import Path
import runpy

import streamlit as st

from core.constants import APP_NAME, VERSION
from core.release_validation import validate_repository
from core.session import initialize_session
from sites.registry import display_names, get_site


ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🕸️",
    layout="wide",
)

initialize_session()

with st.sidebar:
    st.markdown("## DTI SPIDERplan")
    treatment_site = st.selectbox(
        "Treatment site",
        options=display_names(),
        key="unified_treatment_site",
    )
    st.caption(f"Version {VERSION}")
    st.divider()

    with st.expander("Application status", expanded=False):
        issues = validate_repository(ROOT)
        errors = [item for item in issues if item.level == "error"]
        warnings = [item for item in issues if item.level == "warning"]

        if errors:
            st.error(f"{len(errors)} release validation error(s)")
        elif warnings:
            st.warning(f"{len(warnings)} release validation warning(s)")
        else:
            st.success("Repository validation passed")

site = get_site(treatment_site)
site_module = (
    ROOT / "prostate_site.py"
    if site.PROFILE.key == "prostate"
    else ROOT / "head_neck_site.py"
)

if not site_module.exists():
    st.error(
        f"The active {treatment_site} workflow module was not found: "
        f"{site_module.name}"
    )
    st.stop()

# The validated site workflows remain the active rendering layer in Release
# Candidate 1. Shared clinical, comparison, assignment, export, and validation
# systems live under core/, sites/, and ui/.
runpy.run_path(str(site_module), run_name="__main__")
