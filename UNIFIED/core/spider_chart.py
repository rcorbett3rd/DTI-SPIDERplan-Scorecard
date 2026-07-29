"""Shared SPIDER chart façade.

The current Head & Neck chart implementation is already sufficiently generic
for shared chart rendering, so Build 2 exposes it through ``core`` without
changing chart appearance or scoring data.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

import hn_spider_chart as charts


make_spider_chart = charts.make_spider_chart
make_overlay_spider_chart = charts.make_overlay_spider_chart
make_structure_overlay_chart = charts.make_structure_overlay_chart


def render_domain_chart(
    domain_df: pd.DataFrame,
    *,
    name: str = "SPIDERplan",
):
    """Create a single-plan domain SPIDER chart."""

    return charts.make_spider_chart(domain_df, name=name)


def render_comparison_chart(
    domain_a: pd.DataFrame,
    domain_b: pd.DataFrame | None = None,
    *,
    name_a: str = "Plan A",
    name_b: str = "Plan B",
    title: str | None = None,
):
    """Create a shared Plan A/Plan B SPIDER overlay chart."""

    return charts.make_overlay_spider_chart(
        domain_a,
        domain_b,
        name_a=name_a,
        name_b=name_b,
        title=title,
    )
