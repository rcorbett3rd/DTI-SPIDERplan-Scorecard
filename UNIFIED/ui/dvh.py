"""Reusable interactive crosshair DVH chart.

This component preserves the finalized Prostate-style interactive DVH behavior
and accepts the shared `result["dvhs"]` contract used by both current sites.
"""

from __future__ import annotations

from typing import Any, Iterable

import plotly.graph_objects as go


def _normalized_curve(name: str, payload: dict[str, Any]) -> tuple[list[float], list[float]]:
    dose = payload.get("dose_gy", [])
    volume = payload.get("volume_pct", [])
    count = min(len(dose), len(volume))
    return (
        [float(value) for value in dose[:count]],
        [float(value) for value in volume[:count]],
    )


def make_crosshair_dvh(
    dvhs: dict[str, dict[str, Any]],
    *,
    selected_structures: Iterable[str] | None = None,
    title: str = "Interactive DVH",
    plan_name: str | None = None,
    height: int = 620,
) -> go.Figure:
    """Create an interactive cumulative DVH with unified crosshair hovering."""

    selected = (
        list(selected_structures)
        if selected_structures is not None
        else list(dvhs)
    )

    figure = go.Figure()
    for structure_name in selected:
        payload = dvhs.get(structure_name)
        if not payload:
            continue

        dose, volume = _normalized_curve(structure_name, payload)
        if not dose:
            continue

        category = str(payload.get("category", ""))
        legend_name = structure_name
        if plan_name:
            legend_name = f"{plan_name} — {structure_name}"

        figure.add_trace(
            go.Scatter(
                x=dose,
                y=volume,
                mode="lines",
                name=legend_name,
                customdata=[category] * len(dose),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Dose: %{x:.2f} Gy<br>"
                    "Volume: %{y:.2f}%"
                    "<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        title=title,
        height=height,
        xaxis_title="Dose (Gy)",
        yaxis_title="Volume (%)",
        hovermode="x unified",
        legend_title_text="Structures",
        margin=dict(l=55, r=30, t=70, b=55),
    )
    figure.update_xaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        showline=True,
        range=[0, None],
    )
    figure.update_yaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        showline=True,
        range=[0, 105],
    )

    return figure


def make_comparison_crosshair_dvh(
    dvhs_a: dict[str, dict[str, Any]],
    dvhs_b: dict[str, dict[str, Any]],
    *,
    selected_a: Iterable[str] | None = None,
    selected_b: Iterable[str] | None = None,
    plan_a_name: str = "Plan A",
    plan_b_name: str = "Plan B",
    title: str = "Comparison DVH",
) -> go.Figure:
    """Create a Plan A/Plan B DVH overlay with one unified crosshair."""

    figure = make_crosshair_dvh(
        dvhs_a,
        selected_structures=selected_a,
        title=title,
        plan_name=plan_a_name,
    )

    second = make_crosshair_dvh(
        dvhs_b,
        selected_structures=selected_b,
        title=title,
        plan_name=plan_b_name,
    )

    for trace in second.data:
        trace.line = dict(dash="dash")
        figure.add_trace(trace)

    figure.update_layout(title=title, hovermode="x unified")
    return figure
