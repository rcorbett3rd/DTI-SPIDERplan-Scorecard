"""Shared DICOM façade.

This module establishes one stable import path without changing either site's
validated processing behavior. During Build 2, the existing root engines remain
the implementation source of truth:

* ``prostate_dicom_engine.py`` for the finalized Prostate workflow
* ``hn_dicom_parser.py`` for the existing Head & Neck import workflow

Later builds can move implementation code behind this façade without requiring
the UI to change again.
"""

from __future__ import annotations

from typing import Any, Literal

import hn_dicom_parser as head_neck
import prostate_dicom_engine as prostate

SiteKey = Literal["prostate", "head_neck"]


def normalize_site(site: str) -> SiteKey:
    """Normalize display labels and common aliases to an internal site key."""

    value = str(site).strip().lower().replace("&", "and").replace("-", " ")
    value = " ".join(value.split())

    if value in {"prostate", "pros"}:
        return "prostate"
    if value in {"head neck", "head and neck", "hn", "h n"}:
        return "head_neck"

    raise ValueError(f"Unsupported treatment site: {site!r}")


def implementation_for(site: str):
    """Return the current site-specific DICOM implementation module."""

    key = normalize_site(site)
    return prostate if key == "prostate" else head_neck


# Finalized Prostate API re-exported for backward-compatible shared imports.
PlanFiles = prostate.PlanFiles
classify_files = prostate.classify_files
plan_label = prostate.plan_label
treatment_beam_mus = prostate.treatment_beam_mus
fraction_count = prostate.fraction_count
prescription_dose_gy = prostate.prescription_dose_gy
fraction_dose_cgy = prostate.fraction_dose_cgy
modulation_factor = prostate.modulation_factor
structure_names = prostate.structure_names
calculate_dvh = prostate.calculate_dvh
normalize_name = prostate.normalize_name
target_rx_from_name = prostate.target_rx_from_name
is_target = prostate.is_target


# Existing Head & Neck parser API re-exported with explicit names.
save_uploaded_files = head_neck.save_uploaded_files
load_dicoms = head_neck.load_dicoms
classify_rt_files = head_neck.classify_rt_files
extract_plan_summary = head_neck.extract_plan_summary
get_prescription_dose_gy = head_neck.get_prescription_dose_gy
extract_structures = head_neck.extract_structures


def extract_identity(site: str, source: Any) -> dict[str, Any]:
    """Return a minimal, site-independent plan identity dictionary."""

    key = normalize_site(site)

    if key == "prostate":
        return {
            "label": prostate.plan_label(source),
            "fractions": prostate.fraction_count(source),
            "prescription_gy": prostate.prescription_dose_gy(source),
        }

    summary = head_neck.extract_plan_summary(source)
    return {
        "label": summary.get("plan_label", "Unnamed Plan"),
        "name": summary.get("plan_name", ""),
        "fractions": summary.get("fractions_planned") or None,
        "prescription_gy": (
            summary.get("highest_prescription_Gy")
            if isinstance(summary.get("highest_prescription_Gy"), (int, float))
            else None
        ),
    }
