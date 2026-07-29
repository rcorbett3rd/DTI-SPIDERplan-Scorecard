"""Shared reporting façade.

Build 2 preserves the finalized Prostate PDF generator. Head & Neck will be
connected to the same report presentation after its metrics are migrated into
the Prostate interface in later builds.
"""

from __future__ import annotations

from typing import Any

import prostate_reporting


make_pdf = prostate_reporting.make_pdf


def make_site_pdf(site: str, plan_result: dict[str, Any]) -> bytes:
    """Generate a report through the currently validated PDF implementation."""

    normalized = str(site).strip().lower()
    if normalized not in {"prostate", "head & neck", "head and neck", "head_neck"}:
        raise ValueError(f"Unsupported treatment site: {site!r}")

    return prostate_reporting.make_pdf(plan_result)
